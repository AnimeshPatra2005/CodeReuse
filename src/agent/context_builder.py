"""
Context Builder - Manages global and local context for code generation.
"""

from pathlib import Path
from typing import List, Optional, Dict
from src.models.data_models import ContextWindow, Subtask, FunctionNode, SearchResult
from src.indexing.vector_db import VectorDBManager
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class ContextBuilder:
    """Build and manage context windows for LLM code generation."""
    
    def __init__(self, vector_db: VectorDBManager):
        """
        Initialize Context Builder.
        
        Args:
            vector_db: Vector database manager for similarity search
        """
        self.vector_db = vector_db
        config = get_config()
        self.context_config = config.context
        
        # Cumulative subtask memory (function signatures created in previous subtasks)
        self.subtask_memory: List[str] = []
    
    def build_context(
        self,
        subtask: Subtask,
        target_file: str,
        user_request: str
    ) -> ContextWindow:
        """
        Build complete context window for a subtask.
        
        Args:
            subtask: Current subtask to execute
            target_file: Target file for code generation
            user_request: Original user request
            
        Returns:
            ContextWindow with global and local context
        """
        logger.info(f"Building context for subtask {subtask.id}: {subtask.description[:50]}...")
        logger.info(f"[SUBTASK {subtask.id}] Description: {subtask.description}")
        
        # Build global context (target file content)
        global_context = self._build_global_context(target_file)
        
        # Build local context (similar functions from vector DB)
        local_context, retrieval_details = self._build_local_context(subtask, user_request)
        
        # Log retrieval details
        logger.info(f"[SUBTASK {subtask.id}] Semantic similarity threshold: {self.context_config.local.min_similarity}")
        logger.info(f"[SUBTASK {subtask.id}] Retrieved {len(local_context)} functions above threshold")
        
        for detail in retrieval_details:
            logger.info(
                f"[SUBTASK {subtask.id}] Retrieved: {detail['name']} "
                f"[{detail['file']}] similarity: {detail['similarity']:.3f}"
            )
        
        # Create context window
        context = ContextWindow(
            global_context=global_context,
            local_context=local_context,
            subtask_memory=self.subtask_memory.copy(),
            current_subtask=subtask
        )
        
        logger.info(
            f"Context built: {len(local_context)} similar functions, "
            f"{len(self.subtask_memory)} functions in memory"
        )
        
        return context
    
    def _build_global_context(self, target_file: str) -> str:
        """
        Build global context from target file.
        
        Args:
            target_file: Path to target file
            
        Returns:
            File content as string
        """
        if not self.context_config.global_.include_target_file:
            return ""
        
        try:
            file_path = Path(target_file)
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"Loaded target file: {target_file} ({len(content)} chars)")
                return content
            else:
                logger.info(f"Target file does not exist yet: {target_file}")
                return f"# New file: {target_file}\n# File will be created\n"
                
        except Exception as e:
            logger.error(f"Error reading target file {target_file}: {e}")
            return ""
    
    def _build_local_context(self, subtask: Subtask, user_request: str) -> tuple[List[FunctionNode], List[dict]]:
        """
        Build local context by finding similar functions.
        
        Args:
            subtask: Current subtask
            user_request: Original user request
            
        Returns:
            Tuple of (List of similar FunctionNode objects, List of retrieval details)
        """
        # Combine subtask description and user request for better search
        search_query = f"{subtask.description}\n{user_request}"
        
        logger.info(f"Searching vector DB with query: '{subtask.description[:100]}...'")
        
        # Search for similar functions
        search_results = self.vector_db.search_similar(
            query=search_query,
            top_k=10,  # Retrieve more initially
            min_similarity=self.context_config.local.min_similarity,
            max_k=self.context_config.local.max_k,
            dynamic_k=self.context_config.local.dynamic_k
        )
        
        # Extract functions and build retrieval details
        similar_functions = []
        retrieval_details = []
        
        for result in search_results:
            similar_functions.append(result.function)
            retrieval_details.append({
                'name': result.function.name,
                'file': result.function.file_path,
                'similarity': result.similarity_score
            })
        
        logger.info(f"Found {len(similar_functions)} similar functions for subtask")
        
        return similar_functions, retrieval_details
    
    def update_subtask_memory(self, generated_code: str):
        """
        Update subtask memory with newly generated function signatures.
        
        Args:
            generated_code: Code generated in the current subtask
        """
        # Extract function signatures from generated code
        signatures = self._extract_function_signatures(generated_code)
        
        if signatures:
            self.subtask_memory.extend(signatures)
            logger.info(f"Added {len(signatures)} function signatures to memory")
    
    def _extract_function_signatures(self, code: str) -> List[str]:
        """
        Extract function signatures from code.
        
        Args:
            code: Python code string
            
        Returns:
            List of function signatures
        """
        import ast
        
        signatures = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Build signature
                    params = []
                    for arg in node.args.args:
                        param_str = arg.arg
                        if arg.annotation:
                            param_str += f": {ast.unparse(arg.annotation)}"
                        params.append(param_str)
                    
                    signature = f"def {node.name}({', '.join(params)})"
                    
                    if node.returns:
                        signature += f" -> {ast.unparse(node.returns)}"
                    
                    signatures.append(signature)
                    
        except Exception as e:
            logger.warning(f"Error extracting function signatures: {e}")
        
        return signatures
    
    def clear_local_context(self):
        """Clear local context (called after each subtask)."""
        # Local context is ephemeral and rebuilt for each subtask
        # This is a no-op but kept for API consistency
        pass
    
    def reset_memory(self):
        """Reset subtask memory (called at start of new task)."""
        self.subtask_memory.clear()
        logger.info("Subtask memory reset")
    
    def get_context_summary(self, context: ContextWindow) -> str:
        """
        Get a summary of the context window.
        
        Args:
            context: Context window
            
        Returns:
            Summary string
        """
        summary_parts = []
        
        if context.global_context:
            lines = context.global_context.count('\n')
            summary_parts.append(f"Global: {lines} lines")
        
        if context.local_context:
            summary_parts.append(f"Local: {len(context.local_context)} functions")
        
        if context.subtask_memory:
            summary_parts.append(f"Memory: {len(context.subtask_memory)} signatures")
        
        return " | ".join(summary_parts) if summary_parts else "Empty context"
    
    def filter_context_by_relevance(
        self,
        context: ContextWindow,
        min_relevance: float = 0.8
    ) -> ContextWindow:
        """
        Filter local context to keep only highly relevant functions.
        
        Args:
            context: Original context window
            min_relevance: Minimum relevance score
            
        Returns:
            Filtered context window
        """
        # This would require storing relevance scores with functions
        # For now, return as-is
        return context
    
    def add_custom_context(self, context: ContextWindow, custom_text: str) -> ContextWindow:
        """
        Add custom context to the window.
        
        Args:
            context: Original context window
            custom_text: Custom text to add
            
        Returns:
            Updated context window
        """
        updated_global = context.global_context + f"\n\n# Additional Context\n{custom_text}"
        
        return ContextWindow(
            global_context=updated_global,
            local_context=context.local_context,
            subtask_memory=context.subtask_memory,
            current_subtask=context.current_subtask
        )

# Made with Bob
