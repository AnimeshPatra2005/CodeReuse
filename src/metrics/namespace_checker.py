"""
Namespace Invocation Checker - Verifies that generated code reuses existing functions.
"""

import ast
from typing import Set, Dict, Optional, Any
from src.models.data_models import NamespaceResult
from src.indexing.vector_db import VectorDBManager
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class NamespaceChecker:
    """Check namespace invocations to enforce code reuse."""
    
    def __init__(self, vector_db: VectorDBManager):
        """
        Initialize Namespace Checker.
        
        Args:
            vector_db: Vector database manager
        """
        self.vector_db = vector_db
        config = get_config()
        self.min_reuse_score = config.metrics.namespace.min_reuse_score
        
        # Build repository function registry
        self.repo_functions = self._build_function_registry()
    
    def _build_function_registry(self) -> Set[str]:
        """Build set of all function names in repository."""
        functions = self.vector_db.get_all_functions()
        return {func.name for func in functions}
    
    def check(self, generated_code: str, target_file: str) -> NamespaceResult:
        """
        Check namespace invocations in generated code.
        
        Args:
            generated_code: Code to check
            target_file: Target file path
            
        Returns:
            NamespaceResult with reuse metrics
        """
        logger.info("Checking namespace invocations...")
        
        try:
            # Parse generated code
            tree = ast.parse(generated_code)
            
            # Extract all function calls
            called_functions = self._extract_function_calls(tree)
            
            # Find which calls are to repository functions
            repo_functions_used = called_functions.intersection(self.repo_functions)
            
            # Calculate reuse score
            reuse_score = self._calculate_reuse_score(
                called_functions,
                repo_functions_used
            )
            
            # Check if passed
            passed = reuse_score >= self.min_reuse_score
            
            # Build details message
            details = self._build_details_message(
                called_functions,
                repo_functions_used,
                reuse_score,
                passed
            )
            
            result = NamespaceResult(
                called_functions=called_functions,
                repo_functions_used=repo_functions_used,
                reuse_score=reuse_score,
                passed=passed,
                details=details
            )
            
            logger.info(
                f"Namespace check: {len(repo_functions_used)}/{len(called_functions)} "
                f"calls to repo functions (score: {reuse_score:.2%}, "
                f"threshold: {self.min_reuse_score:.2%}) - {'PASSED' if passed else 'FAILED'}"
            )
            
            return result
            
        except SyntaxError as e:
            logger.error(f"Syntax error in generated code: {e}")
            return NamespaceResult(
                called_functions=set(),
                repo_functions_used=set(),
                reuse_score=0.0,
                passed=False,
                details=f"Syntax error: {e}"
            )
        except Exception as e:
            logger.error(f"Error checking namespace: {e}")
            return NamespaceResult(
                called_functions=set(),
                repo_functions_used=set(),
                reuse_score=0.0,
                passed=False,
                details=f"Error: {e}"
            )
    
    def _extract_function_calls(self, tree: ast.AST) -> Set[str]:
        """
        Extract all function calls from AST.
        
        Args:
            tree: AST tree
            
        Returns:
            Set of function names called
        """
        calls = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node.func)
                if call_name:
                    # Extract just the function name (not the full qualified path)
                    # e.g., "module.function" -> "function"
                    if '.' in call_name:
                        call_name = call_name.split('.')[-1]
                    calls.add(call_name)
        
        return calls
    
    def _get_call_name(self, node: ast.AST) -> Optional[str]:
        """
        Get the name of a called function.
        
        Args:
            node: AST node
            
        Returns:
            Function name or None
        """
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                # Handle method calls like obj.method()
                value = self._get_call_name(node.value)
                if value:
                    return f"{value}.{node.attr}"
                return node.attr
            elif isinstance(node, ast.Call):
                return self._get_call_name(node.func)
        except Exception:
            pass
        return None
    
    def _calculate_reuse_score(
        self,
        called_functions: Set[str],
        repo_functions_used: Set[str]
    ) -> float:
        """
        Calculate reuse score.
        
        Formula: |called_functions ∩ repo_functions| / |called_functions|
        
        Args:
            called_functions: All functions called
            repo_functions_used: Repository functions called
            
        Returns:
            Reuse score (0.0 to 1.0)
        """
        if not called_functions:
            # No function calls means simple logic, no penalty
            return 1.0
        
        return len(repo_functions_used) / len(called_functions)
    
    def _build_details_message(
        self,
        called_functions: Set[str],
        repo_functions_used: Set[str],
        reuse_score: float,
        passed: bool
    ) -> str:
        """Build detailed message about namespace check."""
        
        if passed:
            message = f"✓ Namespace check passed (score: {reuse_score:.2%})\n"
        else:
            message = f"✗ Namespace check failed (score: {reuse_score:.2%}, required: {self.min_reuse_score:.2%})\n"
        
        message += f"\nTotal function calls: {len(called_functions)}\n"
        message += f"Repository functions used: {len(repo_functions_used)}\n"
        
        if repo_functions_used:
            message += f"\nRepository functions called:\n"
            for func in sorted(repo_functions_used):
                message += f"  - {func}\n"
        
        # Show functions that could have been reused
        not_reused = called_functions - repo_functions_used
        if not_reused and not passed:
            message += f"\nFunctions not from repository:\n"
            for func in sorted(not_reused):
                message += f"  - {func}\n"
            message += "\nConsider using existing repository functions instead.\n"
        
        return message
    
    def get_reusable_functions(self, query: str, top_k: int = 10) -> Dict[str, str]:
        """
        Get suggestions for reusable functions.
        
        Args:
            query: Search query
            top_k: Number of suggestions
            
        Returns:
            Dict mapping function names to their signatures
        """
        results = self.vector_db.search_similar(
            query=query,
            top_k=top_k,
            min_similarity=0.6,
            dynamic_k=False
        )
        
        suggestions = {}
        for result in results:
            func = result.function
            suggestions[func.name] = func.signature
        
        return suggestions
    
    def analyze_imports(self, generated_code: str) -> Dict[str, Any]:
        """
        Analyze import statements in generated code.
        
        Args:
            generated_code: Code to analyze
            
        Returns:
            Dict with import analysis
        """
        try:
            tree = ast.parse(generated_code)
            
            imports = []
            from_imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'module': alias.name,
                            'alias': alias.asname
                        })
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        from_imports.append({
                            'module': node.module,
                            'names': [alias.name for alias in node.names],
                            'level': node.level
                        })
            
            return {
                'imports': imports,
                'from_imports': from_imports,
                'total_imports': len(imports) + len(from_imports)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing imports: {e}")
            return {
                'imports': [],
                'from_imports': [],
                'total_imports': 0,
                'error': str(e)
            }
    
    def suggest_missing_imports(
        self,
        called_functions: Set[str],
        existing_imports: Set[str]
    ) -> Dict[str, str]:
        """
        Suggest missing imports for called functions.
        
        Args:
            called_functions: Functions called in code
            existing_imports: Already imported modules
            
        Returns:
            Dict mapping function names to suggested import statements
        """
        suggestions = {}
        
        for func_name in called_functions:
            if func_name in self.repo_functions:
                # Find which file contains this function
                functions = self.vector_db.get_all_functions()
                for func in functions:
                    if func.name == func_name:
                        # Suggest import
                        module_path = func.file_path.replace('/', '.').replace('.py', '')
                        suggestions[func_name] = f"from {module_path} import {func_name}"
                        break
        
        return suggestions

# Made with Bob
