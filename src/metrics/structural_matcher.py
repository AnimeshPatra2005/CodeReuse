"""
Structural Similarity Matcher - Detects code plagiarism by comparing AST structures.
"""

import ast
from typing import List, Set, Tuple
from src.models.data_models import StructuralResult, StructuralViolation, FunctionNode
from src.indexing.vector_db import VectorDBManager
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class StructuralMatcher:
    """Detect structural plagiarism in generated code."""
    
    def __init__(self, vector_db: VectorDBManager):
        """
        Initialize Structural Matcher.
        
        Args:
            vector_db: Vector database manager
        """
        self.vector_db = vector_db
        config = get_config()
        self.max_similarity = config.metrics.structural.max_similarity
        self.semantic_threshold = config.metrics.structural.semantic_threshold
    
    def check(self, generated_code: str, target_file: str) -> StructuralResult:
        """
        Check for structural plagiarism in generated code.
        
        Args:
            generated_code: Code to check
            target_file: Target file path
            
        Returns:
            StructuralResult with violations
        """
        logger.info("Checking structural similarity...")
        
        try:
            # Parse generated code
            tree = ast.parse(generated_code)
            
            # Extract functions from generated code
            generated_functions = self._extract_functions(tree)
            
            if not generated_functions:
                logger.info("No functions in generated code to check")
                return StructuralResult(
                    violations=[],
                    max_similarity=0.0,
                    passed=True,
                    details="No functions to check"
                )
            
            # Check each generated function against repository
            violations = []
            max_similarity = 0.0
            
            for gen_func_name, gen_tokens in generated_functions:
                # Search for semantically similar functions
                similar_funcs = self._find_similar_functions(gen_func_name, generated_code)
                
                # Check structural similarity with each
                for repo_func in similar_funcs:
                    repo_tokens = self._extract_structural_tokens_from_function(repo_func)
                    
                    similarity = self._calculate_jaccard_similarity(gen_tokens, repo_tokens)
                    max_similarity = max(max_similarity, similarity)
                    
                    # Check for violation
                    if similarity >= self.max_similarity:
                        violation = StructuralViolation(
                            generated_function=gen_func_name,
                            similar_repo_function=repo_func.name,
                            similarity_score=similarity,
                            repo_file_path=repo_func.file_path,
                            explanation=(
                                f"Generated function '{gen_func_name}' has {similarity:.1%} "
                                f"structural similarity with '{repo_func.name}' from {repo_func.file_path}. "
                                f"This suggests copying logic instead of calling the function. "
                                f"Consider importing and calling '{repo_func.name}' instead."
                            )
                        )
                        violations.append(violation)
            
            passed = len(violations) == 0
            
            details = self._build_details_message(violations, max_similarity, passed)
            
            result = StructuralResult(
                violations=violations,
                max_similarity=max_similarity,
                passed=passed,
                details=details
            )
            
            logger.info(
                f"Structural check: {len(violations)} violations, "
                f"max similarity: {max_similarity:.2%} - {'PASSED' if passed else 'FAILED'}"
            )
            
            return result
            
        except SyntaxError as e:
            logger.error(f"Syntax error in generated code: {e}")
            return StructuralResult(
                violations=[],
                max_similarity=0.0,
                passed=False,
                details=f"Syntax error: {e}"
            )
        except Exception as e:
            logger.error(f"Error checking structural similarity: {e}")
            return StructuralResult(
                violations=[],
                max_similarity=0.0,
                passed=False,
                details=f"Error: {e}"
            )
    
    def _extract_functions(self, tree: ast.AST) -> List[Tuple[str, Set[str]]]:
        """
        Extract functions and their structural tokens.
        
        Args:
            tree: AST tree
            
        Returns:
            List of (function_name, structural_tokens) tuples
        """
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                tokens = self._extract_structural_tokens(node)
                functions.append((node.name, tokens))
        
        return functions
    
    def _extract_structural_tokens(self, func_node: ast.FunctionDef) -> Set[str]:
        """
        Extract structural tokens from a function (AST node types only).
        
        Args:
            func_node: Function AST node
            
        Returns:
            Set of structural tokens
        """
        tokens = set()
        
        for node in ast.walk(func_node):
            # Get node type
            node_type = type(node).__name__
            
            # Skip certain nodes that don't represent structure
            skip_types = {'Load', 'Store', 'Del', 'Name', 'Constant', 'Str', 'Num'}
            if node_type in skip_types:
                continue
            
            # Add node type as token
            tokens.add(node_type)
            
            # For control flow, add more specific tokens
            if isinstance(node, ast.If):
                tokens.add('If_statement')
            elif isinstance(node, ast.For):
                tokens.add('For_loop')
            elif isinstance(node, ast.While):
                tokens.add('While_loop')
            elif isinstance(node, ast.Try):
                tokens.add('Try_except')
            elif isinstance(node, ast.With):
                tokens.add('With_context')
            elif isinstance(node, ast.Return):
                tokens.add('Return_statement')
            elif isinstance(node, ast.Assign):
                tokens.add('Assignment')
            elif isinstance(node, ast.BinOp):
                # Add operator type
                op_type = type(node.op).__name__
                tokens.add(f'BinOp_{op_type}')
            elif isinstance(node, ast.Compare):
                # Add comparison operators
                for op in node.ops:
                    tokens.add(f'Compare_{type(op).__name__}')
        
        return tokens
    
    def _extract_structural_tokens_from_function(self, func: FunctionNode) -> Set[str]:
        """
        Extract structural tokens from a FunctionNode.
        
        Args:
            func: FunctionNode object
            
        Returns:
            Set of structural tokens
        """
        # We need to get the full function code
        # For now, use a simplified approach based on body_preview
        # In production, you'd want to read the actual file
        
        try:
            # Try to parse the body preview
            code = f"def {func.name}():\n    {func.body_preview}"
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return self._extract_structural_tokens(node)
            
            return set()
            
        except Exception as e:
            logger.warning(f"Error extracting tokens from {func.name}: {e}")
            return set()
    
    def _find_similar_functions(self, function_name: str, code_context: str) -> List[FunctionNode]:
        """
        Find semantically similar functions from repository.
        
        Args:
            function_name: Name of generated function
            code_context: Full code context
            
        Returns:
            List of similar FunctionNode objects
        """
        # Search using function name and context
        query = f"{function_name} {code_context[:200]}"
        
        results = self.vector_db.search_similar(
            query=query,
            top_k=5,
            min_similarity=self.semantic_threshold,
            dynamic_k=True
        )
        
        return [result.function for result in results]
    
    def _calculate_jaccard_similarity(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        """
        Calculate Jaccard similarity between two token sets.
        
        Args:
            tokens1: First token set
            tokens2: Second token set
            
        Returns:
            Jaccard similarity (0.0 to 1.0)
        """
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _build_details_message(
        self,
        violations: List[StructuralViolation],
        max_similarity: float,
        passed: bool
    ) -> str:
        """Build detailed message about structural check."""
        
        if passed:
            message = f"✓ Structural check passed (max similarity: {max_similarity:.2%})\n"
            message += "No structural plagiarism detected.\n"
        else:
            message = f"✗ Structural check failed ({len(violations)} violations)\n"
            message += f"Max similarity: {max_similarity:.2%} (threshold: {self.max_similarity:.2%})\n\n"
            
            for i, violation in enumerate(violations, 1):
                message += f"Violation {i}:\n"
                message += f"  Generated: {violation.generated_function}\n"
                message += f"  Similar to: {violation.similar_repo_function} ({violation.repo_file_path})\n"
                message += f"  Similarity: {violation.similarity_score:.2%}\n"
                message += f"  {violation.explanation}\n\n"
        
        return message
    
    def analyze_code_structure(self, code: str) -> dict:
        """
        Analyze the structure of code.
        
        Args:
            code: Python code to analyze
            
        Returns:
            Dict with structure analysis
        """
        try:
            tree = ast.parse(code)
            
            analysis = {
                'total_functions': 0,
                'total_classes': 0,
                'control_flow_statements': 0,
                'assignments': 0,
                'function_calls': 0,
                'imports': 0
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis['total_functions'] += 1
                elif isinstance(node, ast.ClassDef):
                    analysis['total_classes'] += 1
                elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                    analysis['control_flow_statements'] += 1
                elif isinstance(node, ast.Assign):
                    analysis['assignments'] += 1
                elif isinstance(node, ast.Call):
                    analysis['function_calls'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    analysis['imports'] += 1
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing code structure: {e}")
            return {}

# Made with Bob
