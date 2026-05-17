"""
Dependency Graph Builder for tracking imports and function calls.
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from collections import defaultdict
from src.models.data_models import FunctionNode, ImportNode, DependencyGraph
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DependencyGraphBuilder:
    """Build and manage dependency graphs for code analysis."""
    
    def __init__(self):
        self.import_graph: Dict[str, List[str]] = defaultdict(list)
        self.call_graph: Dict[str, List[str]] = defaultdict(list)
        self.function_registry: Dict[str, str] = {}  # function_name -> file_path
        self.reverse_call_graph: Dict[str, List[str]] = defaultdict(list)  # who calls this function
        self.file_functions: Dict[str, List[str]] = defaultdict(list)  # file -> functions defined
    
    def build_graph(
        self,
        functions_by_file: Dict[str, List[FunctionNode]],
        imports_by_file: Dict[str, List[ImportNode]]
    ) -> DependencyGraph:
        """
        Build complete dependency graph from parsed files.
        
        Args:
            functions_by_file: Dict mapping file paths to their functions
            imports_by_file: Dict mapping file paths to their imports
            
        Returns:
            DependencyGraph object
        """
        logger.info("Building dependency graph...")
        
        # Reset graphs
        self.import_graph.clear()
        self.call_graph.clear()
        self.function_registry.clear()
        self.reverse_call_graph.clear()
        self.file_functions.clear()
        
        # Build function registry
        self._build_function_registry(functions_by_file)
        
        # Build import graph
        self._build_import_graph(imports_by_file)
        
        # Build call graph
        self._build_call_graph(functions_by_file)
        
        logger.info(
            f"Dependency graph built: {len(self.function_registry)} functions, "
            f"{len(self.import_graph)} files with imports, "
            f"{len(self.call_graph)} functions with calls"
        )
        
        return DependencyGraph(
            import_graph=dict(self.import_graph),
            call_graph=dict(self.call_graph),
            function_registry=dict(self.function_registry)
        )
    
    def _build_function_registry(self, functions_by_file: Dict[str, List[FunctionNode]]):
        """Build registry mapping function names to file paths."""
        for file_path, functions in functions_by_file.items():
            for func in functions:
                # Handle potential name collisions by using qualified names
                qualified_name = f"{file_path}::{func.name}"
                self.function_registry[qualified_name] = file_path
                
                # Also store simple name (last one wins in case of collision)
                self.function_registry[func.name] = file_path
                
                # Track functions per file
                self.file_functions[file_path].append(func.name)
    
    def _build_import_graph(self, imports_by_file: Dict[str, List[ImportNode]]):
        """Build graph of file-level import dependencies."""
        for file_path, imports in imports_by_file.items():
            imported_modules = set()
            
            for imp in imports:
                # Try to resolve import to actual file path
                resolved_path = self._resolve_import_to_file(imp.module, file_path)
                if resolved_path:
                    imported_modules.add(resolved_path)
                else:
                    # Store module name if can't resolve to file
                    imported_modules.add(imp.module)
            
            self.import_graph[file_path] = list(imported_modules)
    
    def _resolve_import_to_file(self, module: str, importing_file: str) -> Optional[str]:
        """
        Try to resolve an import statement to an actual file path.
        
        Args:
            module: Module name (e.g., 'src.utils.logger')
            importing_file: File doing the importing
            
        Returns:
            Resolved file path or None
        """
        # This is a simplified resolution
        # In production, you'd want more sophisticated module resolution
        
        # Check if it's a relative import
        if module.startswith('.'):
            base_dir = Path(importing_file).parent
            # Handle relative imports
            parts = module.lstrip('.').split('.')
            potential_path = base_dir / '/'.join(parts)
            
            # Try .py extension
            if potential_path.with_suffix('.py').exists():
                return str(potential_path.with_suffix('.py'))
            
            # Try as package
            if (potential_path / '__init__.py').exists():
                return str(potential_path / '__init__.py')
        
        # Try to resolve absolute import
        # Convert module path to file path
        parts = module.split('.')
        potential_path = Path('/'.join(parts))
        
        # Try .py extension
        if potential_path.with_suffix('.py').exists():
            return str(potential_path.with_suffix('.py'))
        
        # Try as package
        if (potential_path / '__init__.py').exists():
            return str(potential_path / '__init__.py')
        
        return None
    
    def _build_call_graph(self, functions_by_file: Dict[str, List[FunctionNode]]):
        """Build graph of function-level call dependencies."""
        for file_path, functions in functions_by_file.items():
            for func in functions:
                caller = f"{file_path}::{func.name}"
                called_functions = []
                
                for call in func.calls:
                    # Try to resolve call to actual function
                    resolved = self._resolve_function_call(call, file_path, func)
                    if resolved:
                        called_functions.append(resolved)
                        # Build reverse graph
                        self.reverse_call_graph[resolved].append(caller)
                
                if called_functions:
                    self.call_graph[caller] = called_functions
    
    def _resolve_function_call(
        self,
        call: str,
        file_path: str,
        caller_func: FunctionNode
    ) -> Optional[str]:
        """
        Resolve a function call to its qualified name.
        
        Args:
            call: Function call name (e.g., 'validate_email' or 'utils.validate')
            file_path: File where call is made
            caller_func: Function making the call
            
        Returns:
            Qualified function name (file::function) or None
        """
        # Check if it's a method call (has dots)
        if '.' in call:
            parts = call.split('.')
            
            # Check if first part is an imported module
            if parts[0] in caller_func.imports_used:
                # Try to find the function in imported modules
                for imp_file in self.import_graph.get(file_path, []):
                    potential_func = f"{imp_file}::{parts[-1]}"
                    if potential_func in self.function_registry:
                        return potential_func
            
            # Could be a method call on an object, harder to resolve
            return None
        
        # Simple function call
        # First check in same file
        same_file_func = f"{file_path}::{call}"
        if same_file_func in self.function_registry:
            return same_file_func
        
        # Check in imported files
        for imp_file in self.import_graph.get(file_path, []):
            potential_func = f"{imp_file}::{call}"
            if potential_func in self.function_registry:
                return potential_func
        
        # Check global registry (might be from standard library or external)
        if call in self.function_registry:
            target_file = self.function_registry[call]
            return f"{target_file}::{call}"
        
        return None
    
    def get_dependents(self, function_qualified_name: str) -> List[str]:
        """
        Get all functions that depend on (call) the given function.
        
        Args:
            function_qualified_name: Qualified function name (file::function)
            
        Returns:
            List of qualified function names that call this function
        """
        return self.reverse_call_graph.get(function_qualified_name, [])
    
    def get_dependencies(self, function_qualified_name: str) -> List[str]:
        """
        Get all functions that the given function depends on (calls).
        
        Args:
            function_qualified_name: Qualified function name (file::function)
            
        Returns:
            List of qualified function names called by this function
        """
        return self.call_graph.get(function_qualified_name, [])
    
    def get_transitive_dependencies(
        self,
        function_qualified_name: str,
        max_depth: int = 5
    ) -> Set[str]:
        """
        Get all transitive dependencies of a function.
        
        Args:
            function_qualified_name: Qualified function name
            max_depth: Maximum depth to traverse
            
        Returns:
            Set of all transitively called functions
        """
        visited = set()
        to_visit = [(function_qualified_name, 0)]
        
        while to_visit:
            current, depth = to_visit.pop(0)
            
            if current in visited or depth >= max_depth:
                continue
            
            visited.add(current)
            
            # Add direct dependencies
            deps = self.get_dependencies(current)
            for dep in deps:
                if dep not in visited:
                    to_visit.append((dep, depth + 1))
        
        # Remove the starting function itself
        visited.discard(function_qualified_name)
        return visited
    
    def get_function_dependencies(self, file_path: str, function_name: str) -> Dict[str, Any]:
        """
        Get comprehensive dependency information for a function.
        
        Args:
            file_path: File containing the function
            function_name: Name of the function
            
        Returns:
            Dict with dependency information
        """
        qualified_name = f"{file_path}::{function_name}"
        
        return {
            'qualified_name': qualified_name,
            'direct_dependencies': self.get_dependencies(qualified_name),
            'direct_dependents': self.get_dependents(qualified_name),
            'transitive_dependencies': list(self.get_transitive_dependencies(qualified_name)),
            'file_imports': self.import_graph.get(file_path, [])
        }
    
    def get_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """
        Get all dependencies for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dict with file dependency information
        """
        functions = self.file_functions.get(file_path, [])
        
        all_deps = set()
        all_dependents = set()
        
        for func_name in functions:
            qualified = f"{file_path}::{func_name}"
            all_deps.update(self.get_dependencies(qualified))
            all_dependents.update(self.get_dependents(qualified))
        
        return {
            'file_path': file_path,
            'functions': functions,
            'imports': self.import_graph.get(file_path, []),
            'all_function_dependencies': list(all_deps),
            'all_function_dependents': list(all_dependents)
        }
    
    def save_to_file(self, output_path: str):
        """
        Save dependency graph to JSON file.
        
        Args:
            output_path: Path to output file
        """
        graph_data = {
            'import_graph': dict(self.import_graph),
            'call_graph': dict(self.call_graph),
            'function_registry': dict(self.function_registry),
            'reverse_call_graph': dict(self.reverse_call_graph),
            'file_functions': dict(self.file_functions)
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        logger.info(f"Dependency graph saved to {output_path}")
    
    def load_from_file(self, input_path: str):
        """
        Load dependency graph from JSON file.
        
        Args:
            input_path: Path to input file
        """
        with open(input_path, 'r') as f:
            graph_data = json.load(f)
        
        self.import_graph = defaultdict(list, graph_data['import_graph'])
        self.call_graph = defaultdict(list, graph_data['call_graph'])
        self.function_registry = graph_data['function_registry']
        self.reverse_call_graph = defaultdict(list, graph_data['reverse_call_graph'])
        self.file_functions = defaultdict(list, graph_data['file_functions'])
        
        logger.info(f"Dependency graph loaded from {input_path}")

# Made with Bob
