"""
Agent Orchestrator - Main workflow coordinator for code generation.
Uses IBM Granite models via Hugging Face for code generation.
"""

import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from src.models.data_models import (
    GenerationRequest, GenerationResponse, Subtask,
    AgentMode, MetricResult, ContextWindow
)
from src.agent.context_builder import ContextBuilder
from src.indexing.vector_db import VectorDBManager
from src.indexing.dependency_graph import DependencyGraphBuilder
from src.utils.granite_client import GraniteClient
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class Agent:
    """Main agent orchestrator for context-aware code generation with IBM Granite."""
    
    def __init__(
        self,
        vector_db: VectorDBManager,
        dependency_graph: DependencyGraphBuilder,
        api_key: Optional[str] = None
    ):
        """
        Initialize Agent.
        
        Args:
            vector_db: Vector database manager
            dependency_graph: Dependency graph builder
            api_key: Hugging Face API token (optional, reads from env)
        """
        self.vector_db = vector_db
        self.dependency_graph = dependency_graph
        
        # Load config
        config = get_config()
        self.agent_config = config.agent
        self.mode = AgentMode(self.agent_config.mode)
        
        from src.agent.subtask_decomposer import SubtaskDecomposer
        # Initialize components
        self.context_builder = ContextBuilder(vector_db)
        self.decomposer = SubtaskDecomposer(api_key=api_key)
        
        # Initialize IBM Granite client
        self.granite_client = GraniteClient(api_token=api_key)
        
        # Get system prompt from config
        prompt_config = getattr(self.agent_config, 'prompt', None)
        self.system_prompt = getattr(prompt_config, 'system_role',
            "You are a senior software architect who values code reuse and maintainability.") if prompt_config else "You are a senior software architect who values code reuse and maintainability."
        
        # Metrics orchestrator (will be initialized when needed)
        self.metrics_orchestrator = None
        
        # LLM validator (will be initialized when needed)
        self.llm_validator = None
    
    def generate_code(self, request: GenerationRequest) -> GenerationResponse:
        """
        Main entry point for code generation.
        
        Args:
            request: Generation request
            
        Returns:
            Generation response with code and metrics
        """
        logger.info(f"Starting code generation in {request.mode} mode")
        start_time = time.time()
        
        try:
            # Override mode if specified in request
            if request.mode:
                self.mode = request.mode
            
            # Reset context builder memory
            self.context_builder.reset_memory()
            
            # Step 1: Decompose task into subtasks
            decomposition = self.decomposer.decompose(
                request.user_request,
                request.target_file
            )
            
            if not self.decomposer.validate_subtasks(decomposition.subtasks):
                logger.error("Invalid subtasks generated")
                return self._create_error_response(
                    "Failed to decompose task into valid subtasks",
                    decomposition.subtasks
                )
            
            # Reorder subtasks by dependencies
            subtasks = self.decomposer.reorder_by_dependencies(decomposition.subtasks)
            
            # Step 2: Execute subtasks sequentially
            all_generated_code = []
            all_similar_functions = []
            final_metrics = None
            
            for subtask in subtasks:
                logger.info(f"Executing subtask {subtask.id}/{len(subtasks)}: {subtask.description}")
                
                # Build context for this subtask
                context = self.context_builder.build_context(
                    subtask,
                    request.target_file,
                    request.user_request
                )
                
                # Generate code for subtask
                code, similar_funcs = self._generate_code_for_subtask(
                    subtask,
                    context,
                    request
                )
                
                if code:
                    all_generated_code.append(code)
                    all_similar_functions.extend(similar_funcs)
                    
                    # Update subtask memory with generated functions
                    self.context_builder.update_subtask_memory(code)
                    
                    # Validate in Legacy mode
                    if self.mode == AgentMode.LEGACY:
                        metrics = self._validate_code(code, request.target_file)
                        if metrics and not metrics.passed:
                            logger.warning(f"Subtask {subtask.id} failed validation")
                            # In production, implement retry logic here
                        final_metrics = metrics
                
                # Clear local context (ephemeral)
                self.context_builder.clear_local_context()
            
            # Step 3: Combine all generated code
            final_code = self._combine_code_blocks(all_generated_code)
            
            logger.info(f"Generated {len(final_code)} characters of code")
            
            # Step 4: Final validation (Legacy mode only)
            if self.mode == AgentMode.LEGACY and final_code:
                final_metrics = self._validate_code(final_code, request.target_file)
                
                # Step 5: LLM-based dependent file validation
                if final_metrics and final_metrics.passed:
                    llm_validation = self._validate_with_llm(final_code, request.target_file)
                    logger.info(f"[LLM VALIDATION] {llm_validation['report']}")
                    
                    # Store LLM validation in metrics
                    if hasattr(final_metrics, 'llm_validation'):
                        final_metrics.llm_validation = llm_validation
            
            execution_time = time.time() - start_time
            
            return GenerationResponse(
                generated_code=final_code,
                subtasks=subtasks,
                metrics=final_metrics,
                similar_functions_used=all_similar_functions,
                execution_time=execution_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error during code generation: {e}")
            execution_time = time.time() - start_time
            
            return GenerationResponse(
                generated_code="",
                subtasks=[],
                metrics=None,
                similar_functions_used=[],
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def _generate_code_for_subtask(
        self,
        subtask: Subtask,
        context: ContextWindow,
        request: GenerationRequest
    ) -> tuple[str, List]:
        """
        Generate code for a single subtask.
        
        Args:
            subtask: Subtask to execute
            context: Context window
            request: Original request
            
        Returns:
            Tuple of (generated_code, similar_functions_used)
        """
        # Build prompt
        prompt = self._build_generation_prompt(subtask, context, request)
        
        try:
            # Generate code with LLM (Granite)
            response_text = self.granite_client.generate_with_retry(
                prompt=prompt,
                temperature=self.agent_config.llm.temperature,
                max_tokens=self.agent_config.llm.max_tokens,
                max_retries=3
            )
            
            # Extract code from response
            code = self._extract_code_from_response(response_text)
            
            logger.info(f"Generated {len(code)} characters of code for subtask {subtask.id}")
            
            return code, context.local_context
            
        except Exception as e:
            logger.error(f"Error generating code for subtask {subtask.id}: {e}")
            return "", []
    
    def _build_generation_prompt(
        self,
        subtask: Subtask,
        context: ContextWindow,
        request: GenerationRequest
    ) -> str:
        """Build prompt for code generation."""
        
        # Get context string
        context_str = context.get_context_string()
        
        # Build mode-specific instructions
        if self.mode == AgentMode.LEGACY:
            mode_instructions = """
**IMPORTANT - CODE REUSE REQUIREMENTS:**
1. You MUST reuse existing functions from the "SIMILAR EXISTING FUNCTIONS" section
2. Call these functions instead of reimplementing their logic
3. Import them properly at the top of your code
4. Do NOT copy-paste their implementation
5. Your code will be validated for reuse - minimum 40% of function calls must be to existing functions

**Validation Criteria:**
- Namespace Reuse: At least 40% of your function calls must be to existing repository functions
- No Structural Plagiarism: Do not copy the internal logic of existing functions
- Proper Imports: Include all necessary import statements
"""
        else:
            mode_instructions = """
**GREENFIELD MODE:**
You are creating new functionality. Focus on:
1. Clean, maintainable code
2. Proper error handling
3. Clear documentation
4. Following Python best practices
"""
        
        prompt = f"""You are an expert Python developer. Generate high-quality Python code for the following subtask.

**Original User Request:**
{request.user_request}

**Current Subtask ({subtask.id}):**
{subtask.description}

**Complexity:** {subtask.estimated_complexity}

{mode_instructions}

{context_str}

**Requirements:**
1. Generate ONLY Python code, no explanations
2. Include proper imports
3. Add docstrings and type hints
4. Follow PEP 8 style guidelines
5. Handle errors appropriately
6. Write production-ready code

**Output Format:**
Return ONLY the Python code wrapped in ```python code blocks. No additional text.

Example:
```python
# Your code here
import existing_module

def new_function():
    \"\"\"Docstring\"\"\"
    result = existing_module.existing_function()
    return result
```

Now generate the code for the subtask above.
"""
        
        return prompt
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """Extract Python code from LLM response."""
        import re
        
        # Try to find code in markdown code blocks
        code_match = re.search(r'```python\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Try generic code blocks
        code_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # If no code blocks, return the whole response (might be just code)
        return response_text.strip()
    
    def _validate_code(self, code: str, target_file: str) -> Optional[MetricResult]:
        """
        Validate generated code (Legacy mode only).
        
        Args:
            code: Generated code
            target_file: Target file path
            
        Returns:
            MetricResult or None
        """
        if self.mode != AgentMode.LEGACY:
            return None
        
        # Import metrics orchestrator lazily to avoid circular imports
        if self.metrics_orchestrator is None:
            from src.metrics.metric import MetricOrchestrator
            self.metrics_orchestrator = MetricOrchestrator(
                self.vector_db,
                self.dependency_graph
            )
        
        try:
            result = self.metrics_orchestrator.validate(code, target_file)
            return result
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return None
    
    def _validate_with_llm(self, code: str, target_file: str) -> Dict[str, Any]:
        """
        Validate generated code with LLM against dependent files.
        
        Args:
            code: Generated code
            target_file: Target file path
            
        Returns:
            Dict with LLM validation results
        """
        # Import LLM validator lazily
        if self.llm_validator is None:
            from src.metrics.llm_validator import LLMValidator
            self.llm_validator = LLMValidator(
                self.dependency_graph,
                api_key=self.granite_client.api_token
            )
        
        try:
            logger.info("Starting LLM-based dependent file validation...")
            result = self.llm_validator.validate_with_dependents(target_file, code)
            
            # Log dependent files
            if result['dependent_files']:
                logger.info(f"Found {len(result['dependent_files'])} dependent files:")
                for dep_file in result['dependent_files']:
                    logger.info(f"  - {dep_file}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during LLM validation: {e}")
            return {
                'passed': False,
                'report': f'LLM validation error: {str(e)}',
                'dependent_files': [],
                'issues': []
            }
    
    def _combine_code_blocks(self, code_blocks: List[str]) -> str:
        """
        Combine multiple code blocks into final code.
        
        Args:
            code_blocks: List of code strings
            
        Returns:
            Combined code string
        """
        if not code_blocks:
            return ""
        
        # Simple combination - in production, you'd want smarter merging
        # (deduplicate imports, organize functions, etc.)
        
        combined = "\n\n".join(code_blocks)
        
        # Basic cleanup: deduplicate imports
        combined = self._deduplicate_imports(combined)
        
        return combined
    
    def _deduplicate_imports(self, code: str) -> str:
        """Remove duplicate import statements."""
        import ast
        
        try:
            tree = ast.parse(code)
            
            # Extract all imports
            imports = []
            other_nodes = []
            
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_str = ast.unparse(node)
                    if import_str not in imports:
                        imports.append(import_str)
                else:
                    other_nodes.append(ast.unparse(node))
            
            # Reconstruct code with deduplicated imports
            result = "\n".join(imports)
            if imports and other_nodes:
                result += "\n\n"
            result += "\n\n".join(other_nodes)
            
            return result
            
        except Exception as e:
            logger.warning(f"Error deduplicating imports: {e}")
            return code
    
    def _create_error_response(
        self,
        error_message: str,
        subtasks: List[Subtask]
    ) -> GenerationResponse:
        """Create error response."""
        return GenerationResponse(
            generated_code="",
            subtasks=subtasks,
            metrics=None,
            similar_functions_used=[],
            execution_time=0.0,
            success=False,
            error_message=error_message
        )
    
    def generate_code_simple(self, query: str, target_file: str, mode: str = "legacy") -> dict:
        """
        Simplified interface for demo - generates code and returns as dict.
        
        Args:
            query: User query/request
            target_file: Target file path
            mode: Agent mode (legacy or greenfield)
            
        Returns:
            Dict with 'code' and 'response' keys
        """
        # Create request
        request = GenerationRequest(
            user_request=query,
            target_file=target_file,
            mode=AgentMode(mode)
        )
        
        # Generate code
        response = self.generate_code(request)
        
        # Return simplified dict format
        return {
            "code": response.generated_code,
            "response": response
        }

# Made with Bob
