"""
Simplified Agent for MVP - Single task generation with IBM Granite
No subtask decomposition, direct code generation with proper context
"""

import time
from typing import Optional, Dict, Any
from pathlib import Path
from src.models.data_models import AgentMode
from src.agent.context_builder import ContextBuilder
from src.indexing.vector_db import VectorDBManager
from src.indexing.dependency_graph import DependencyGraphBuilder
from src.utils.granite_client import GraniteClient
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class SimpleAgent:
    """Simplified agent for MVP - single task code generation with IBM Granite."""
    
    def __init__(
        self,
        vector_db: VectorDBManager,
        dependency_graph: DependencyGraphBuilder,
        api_key: Optional[str] = None,
        repo_path: Optional[str] = None,
        metrics_orchestrator=None
    ):
        """
        Initialize Simple Agent.
        
        Args:
            vector_db: Vector database manager
            dependency_graph: Dependency graph builder
            api_key: Hugging Face API token (optional, reads from env)
            repo_path: Absolute path to the repository root (used to resolve target files)
            metrics_orchestrator: MetricOrchestrator instance for code validation
        """
        self.vector_db = vector_db
        self.dependency_graph = dependency_graph
        # Bug #2 fix: store repo root so target files can be resolved correctly
        self.repo_path = Path(repo_path) if repo_path else None
        
        # Load config
        config = get_config()
        self.agent_config = config.agent
        self.mode = AgentMode(self.agent_config.mode)
        
        # Initialize components
        self.context_builder = ContextBuilder(vector_db)
        
        # Initialize IBM Granite client
        self.granite_client = GraniteClient(api_token=api_key)
        
        # Get system prompt from config
        try:
            self.system_prompt = config.agent.prompt.system_role
        except:
            self.system_prompt = (
                "You are a senior software architect who values code reuse and maintainability. "
                "You strongly prefer reusing existing functions over writing new code, as more code "
                "means more maintenance and auditing. Your goal is to leverage existing components "
                "whenever possible."
            )
        
        # Bug #4 fix: metrics_orchestrator is now injected, not left as None forever
        self.metrics_orchestrator = metrics_orchestrator
    
    def generate_code_simple(
        self,
        query: str,
        target_file: str,
        mode: str = "legacy"
    ) -> Dict[str, Any]:
        """
        Generate code for a single task (MVP version - no subtask decomposition).
        
        Args:
            query: User query/request
            target_file: Target file path
            mode: Agent mode (legacy or greenfield)
            
        Returns:
            Dict with 'code' and 'response' keys
        """
        logger.info(f"Starting simple code generation: {query}")
        start_time = time.time()
        
        try:
            # Set mode
            self.mode = AgentMode(mode)
            
            # Step 1: Read target file (global context)
            global_context = self._read_target_file(target_file)
            
            # Step 2: Get similar functions (local context)
            similar_functions = self.vector_db.search_similar(
                query=query,
                top_k=10,
                min_similarity=0.7,
                max_k=5
            )
            
            logger.info(f"Found {len(similar_functions)} similar functions")
            
            # Step 3: Build prompt with proper context structure
            prompt = self._build_prompt(
                query=query,
                target_file=target_file,
                global_context=global_context,
                similar_functions=similar_functions
            )
            
            # Step 4: Generate code with IBM Granite
            logger.info("Generating code with IBM Granite...")
            generated_text = self.granite_client.generate_with_retry(
                prompt=prompt,
                max_retries=3,
                retry_delay=2.0
            )
            
            # Step 5: Extract code from response
            code = self._extract_code(generated_text)
            
            # Step 6: Validate if in legacy mode
            if self.mode == AgentMode.LEGACY and self.metrics_orchestrator:
                logger.info("Validating generated code...")
                metrics = self.metrics_orchestrator.validate(
                    generated_code=code,
                    target_file=target_file,
                    mode=self.mode
                )
            else:
                metrics = None
            
            elapsed_time = time.time() - start_time
            logger.info(f"Code generation completed in {elapsed_time:.2f}s")
            
            return {
                "code": code,
                "response": {
                    "generated_code": code,
                    "similar_functions": [sf.function for sf in similar_functions],
                    "metrics": metrics,
                    "execution_time": elapsed_time,
                    "success": True
                }
            }
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return {
                "code": "",
                "response": {
                    "generated_code": "",
                    "similar_functions": [],
                    "metrics": None,
                    "execution_time": time.time() - start_time,
                    "success": False,
                    "error": str(e)
                }
            }
    
    def _read_target_file(self, target_file: str) -> str:
        """Read target file content (global context).
        
        Bug #2 fix: resolve target_file relative to repo_path when provided,
        so paths like 'services/user_service.py' resolve correctly.
        """
        try:
            file_path = Path(target_file)
            
            # If path is not absolute and we have a repo root, resolve against it
            if not file_path.is_absolute() and self.repo_path:
                resolved = self.repo_path / file_path
                if resolved.exists():
                    file_path = resolved
                elif not file_path.exists():
                    logger.warning(
                        f"Target file not found at '{target_file}' or "
                        f"'{resolved}'. Continuing without global context."
                    )
                    return ""
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"Read target file: {file_path} ({len(content)} chars)")
                return content
            else:
                logger.warning(f"Target file not found: {target_file}")
                return ""
        except Exception as e:
            logger.error(f"Error reading target file: {e}")
            return ""
    
    def _build_prompt(
        self,
        query: str,
        target_file: str,
        global_context: str,
        similar_functions: list
    ) -> str:
        """
        Build prompt with proper global + local context structure.
        Following the architecture: system prompt + global context + local context + task
        """
        
        # Build similar functions context
        local_context = ""
        if similar_functions:
            local_context = "\n=== EXISTING FUNCTIONS YOU MUST REUSE ===\n"
            local_context += "These functions already exist in the repository. You MUST call them instead of reimplementing:\n\n"
            
            for i, search_result in enumerate(similar_functions, 1):
                func = search_result.function
                local_context += f"{i}. Function: {func.name}\n"
                local_context += f"   File: {func.file_path}\n"
                local_context += f"   Signature: {func.signature}\n"
                if func.docstring:
                    local_context += f"   Purpose: {func.docstring}\n"
                local_context += f"   Similarity: {search_result.similarity_score:.2%}\n\n"
        
        # Build mode-specific instructions
        if self.mode == AgentMode.LEGACY:
            mode_instructions = """
**CRITICAL REQUIREMENTS - CODE REUSE:**
1. You MUST reuse the existing functions listed above
2. Call these functions instead of reimplementing their logic
3. Import them properly at the top of your code
4. Do NOT copy-paste or reimplement their internal logic
5. Minimum 40% of your function calls must be to existing repository functions

**Why Code Reuse Matters:**
- Less code = less maintenance
- Less code = less auditing
- Reusing tested functions = more reliable code
- You are a senior architect who understands this principle
"""
        else:
            mode_instructions = """
**GREENFIELD MODE:**
You are creating new functionality from scratch.
Focus on clean, maintainable, well-documented code.
"""
        
        # Build complete prompt
        prompt = f"""{self.system_prompt}

=== TASK ===
{query}

=== TARGET FILE: {target_file} ===
{global_context if global_context else "# New file - no existing content"}

{local_context}

{mode_instructions}

**Instructions:**
1. Analyze the existing functions above
2. Determine which ones you can reuse for this task
3. Generate Python code that calls these existing functions
4. Include proper imports for the functions you're calling
5. Add docstrings and type hints
6. Follow PEP 8 style guidelines

**Output Format:**
Return ONLY the Python code wrapped in ```python code blocks. No explanations, no additional text.

Example:
```python
from utils.validators import validate_email
from services.user_service import get_user

def new_function(email: str):
    \"\"\"New function that reuses existing utilities.\"\"\"
    if not validate_email(email):
        raise ValueError("Invalid email")
    return get_user(email)
```

Now generate the code:
"""
        
        return prompt
    
    def _extract_code(self, response_text: str) -> str:
        """Extract Python code from response."""
        # Look for code blocks
        if "```python" in response_text:
            start = response_text.find("```python") + 9
            end = response_text.find("```", start)
            if end != -1:
                code = response_text[start:end].strip()
                logger.info(f"Extracted {len(code)} characters of code")
                return code
        
        # If no code block, try to find code-like content
        lines = response_text.strip().split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            # Start of code (imports, def, class, etc.)
            if line.strip().startswith(('import ', 'from ', 'def ', 'class ', '@')):
                in_code = True
            
            if in_code:
                code_lines.append(line)
        
        if code_lines:
            code = '\n'.join(code_lines)
            logger.info(f"Extracted {len(code)} characters of code (no markers)")
            return code
        
        # Fallback: return entire response
        logger.warning("Could not extract code, returning full response")
        return response_text.strip()


# Made with Bob