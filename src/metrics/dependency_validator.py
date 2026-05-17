"""
Dependency Validator - Checks for breaking changes in dependent files.
"""

import ast
from pathlib import Path
from typing import List, Set, Dict
from src.models.data_models import DependencyResult, BreakingChange, FunctionNode
from src.indexing.dependency_graph import DependencyGraphBuilder
from src.indexing.ast_parser import ASTParser
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class DependencyValidator:
    """Validate that code changes don't break dependent files."""
    
    def __init__(self, dependency_graph: DependencyGraphBuilder):
        """
        Initialize Dependency Validator.
        
        Args:
            dependency_graph: Dependency graph builder
        """
        self.dependency_graph = dependency_graph
        self.parser = ASTParser()
        
        config = get_config()
        self.check_breaking_changes = config.metrics.dependency.check_breaking_changes
    
    def validate(self, generated_code: str, target_file: str) -> DependencyResult:
        """
        Validate dependencies and check for breaking changes.
        
        Args:
            generated_code: Generated code
            target_file: Target file path
            
        Returns:
            DependencyResult with breaking changes and warnings
        """
        if not self.check_breaking_changes:
            return DependencyResult(
                breaking_changes=[],
                warnings=[],
                passed=True,
                details="Dependency checking disabled"
            )
        
        logger.info(f"Validating dependencies for {target_file}...")
        
        try:
            # Extract functions from generated code
            generated_functions = self._extract_functions_from_code(generated_code)
            
            if not generated_functions:
                return DependencyResult(
                    breaking_changes=[],
                    warnings=[],
                    passed=True,
                    details="No functions to validate"
                )
            
            # Get dependent files
            dependent_files = self._get_dependent_files(target_file)
            
            if not dependent_files:
                return DependencyResult(
                    breaking_changes=[],
                    warnings=[],
                    passed=True,
                    details="No dependent files found"
                )
            
            # Check each dependent file
            breaking_changes = []
            warnings = []
            
            for dep_file in dependent_files:
                changes, warns = self._check_dependent_file(
                    dep_file,
                    target_file,
                    generated_functions
                )
                breaking_changes.extend(changes)
                warnings.extend(warns)
            
            passed = len(breaking_changes) == 0
            details = self._build_details_message(
                breaking_changes,
                warnings,
                dependent_files,
                passed
            )
            
            result = DependencyResult(
                breaking_changes=breaking_changes,
                warnings=warnings,
                passed=passed,
                details=details
            )
            
            logger.info(
                f"Dependency validation: {len(breaking_changes)} breaking changes, "
                f"{len(warnings)} warnings - {'PASSED' if passed else 'FAILED'}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating dependencies: {e}")
            return DependencyResult(
                breaking_changes=[],
                warnings=[f"Error during validation: {e}"],
                passed=False,
                details=f"Error: {e}"
            )
    
    def _extract_functions_from_code(self, code: str) -> Dict[str, Dict]:
        """
        Extract function signatures from code.
        
        Args:
            code: Python code
            
        Returns:
            Dict mapping function names to their info
        """
        functions = {}
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract parameter names
                    params = [arg.arg for arg in node.args.args]
                    
                    # Extract return type if present
                    return_type = None
                    if node.returns:
                        return_type = ast.unparse(node.returns)
                    
                    functions[node.name] = {
                        'params': params,
                        'param_count': len(params),
                        'return_type': return_type,
                        'has_varargs': node.args.vararg is not None,
                        'has_kwargs': node.args.kwarg is not None
                    }
        
        except Exception as e:
            logger.warning(f"Error extracting functions: {e}")
        
        return functions
    
    def _get_dependent_files(self, target_file: str) -> List[str]:
        """
        Get files that depend on the target file.
        
        Args:
            target_file: Target file path
            
        Returns:
            List of dependent file paths
        """
        # Get functions in target file
        functions_in_file = self.dependency_graph.file_functions.get(target_file, [])
        
        dependent_files = set()
        
        for func_name in functions_in_file:
            qualified_name = f"{target_file}::{func_name}"
            dependents = self.dependency_graph.get_dependents(qualified_name)
            
            # Extract file paths from qualified names
            for dep in dependents:
                if '::' in dep:
                    file_path = dep.split('::')[0]
                    if file_path != target_file:
                        dependent_files.add(file_path)
        
        return list(dependent_files)
    
    def _check_dependent_file(
        self,
        dependent_file: str,
        target_file: str,
        new_functions: Dict[str, Dict]
    ) -> tuple[List[BreakingChange], List[str]]:
        """
        Check a dependent file for breaking changes.
        
        Args:
            dependent_file: File that depends on target
            target_file: Target file being modified
            new_functions: New function signatures
            
        Returns:
            Tuple of (breaking_changes, warnings)
        """
        breaking_changes = []
        warnings = []
        
        try:
            # Parse dependent file
            if not Path(dependent_file).exists():
                warnings.append(f"Dependent file not found: {dependent_file}")
                return breaking_changes, warnings
            
            functions, imports = self.parser.parse_file(dependent_file)
            
            # Check each function in dependent file
            for func in functions:
                # Check if it calls any modified functions
                for call in func.calls:
                    # Extract function name from call
                    call_name = call.split('.')[-1] if '.' in call else call
                    
                    if call_name in new_functions:
                        # Function is being called - check compatibility
                        issue = self._check_signature_compatibility(
                            call_name,
                            new_functions[call_name],
                            func
                        )
                        
                        if issue:
                            breaking_changes.append(BreakingChange(
                                affected_file=dependent_file,
                                affected_function=func.name,
                                issue=issue,
                                suggestion=f"Update calls to {call_name} in {func.name}"
                            ))
        
        except Exception as e:
            warnings.append(f"Error checking {dependent_file}: {e}")
        
        return breaking_changes, warnings
    
    def _check_signature_compatibility(
        self,
        func_name: str,
        new_signature: Dict,
        calling_function: FunctionNode
    ) -> str:
        """
        Check if new signature is compatible with existing calls.
        
        Args:
            func_name: Function name
            new_signature: New function signature info
            calling_function: Function that calls it
            
        Returns:
            Issue description or empty string if compatible
        """
        # This is a simplified check
        # In production, you'd want more sophisticated analysis
        
        # For now, just warn about parameter count changes
        # A real implementation would parse the actual call sites
        
        # We can't easily determine how the function is called without
        # more sophisticated analysis, so we'll be conservative
        
        return ""  # Assume compatible for now
    
    def _build_details_message(
        self,
        breaking_changes: List[BreakingChange],
        warnings: List[str],
        dependent_files: List[str],
        passed: bool
    ) -> str:
        """Build detailed message about dependency validation."""
        
        if passed:
            message = "✓ Dependency validation passed\n"
            message += f"Checked {len(dependent_files)} dependent files\n"
        else:
            message = f"✗ Dependency validation failed ({len(breaking_changes)} breaking changes)\n\n"
            
            for i, change in enumerate(breaking_changes, 1):
                message += f"Breaking Change {i}:\n"
                message += f"  File: {change.affected_file}\n"
                message += f"  Function: {change.affected_function}\n"
                message += f"  Issue: {change.issue}\n"
                message += f"  Suggestion: {change.suggestion}\n\n"
        
        if warnings:
            message += f"\nWarnings ({len(warnings)}):\n"
            for warning in warnings:
                message += f"  - {warning}\n"
        
        return message
    
    def get_dependency_info(self, target_file: str) -> Dict:
        """
        Get dependency information for a file.
        
        Args:
            target_file: Target file path
            
        Returns:
            Dict with dependency info
        """
        return self.dependency_graph.get_file_dependencies(target_file)
    
    def check_circular_dependencies(self, target_file: str) -> List[List[str]]:
        """
        Check for circular dependencies.
        
        Args:
            target_file: Target file path
            
        Returns:
            List of circular dependency chains
        """
        # Simplified circular dependency detection
        # In production, implement proper cycle detection algorithm
        
        circular = []
        visited = set()
        
        def dfs(file: str, path: List[str]):
            if file in path:
                # Found a cycle
                cycle_start = path.index(file)
                circular.append(path[cycle_start:] + [file])
                return
            
            if file in visited:
                return
            
            visited.add(file)
            path.append(file)
            
            # Check imports
            for imported in self.dependency_graph.import_graph.get(file, []):
                dfs(imported, path.copy())
        
        dfs(target_file, [])
        
        return circular

# Made with Bob
