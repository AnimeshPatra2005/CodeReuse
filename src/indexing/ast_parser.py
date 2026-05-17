"""
AST Parser for extracting functions, imports, and calls from Python code.
"""

import ast
import re
from pathlib import Path
from typing import List, Set, Optional, Tuple
from src.models.data_models import FunctionNode, ImportNode
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ASTParser:
    """Parse Python files and extract code elements."""
    
    def __init__(self):
        self.current_file = ""
    
    def parse_file(self, file_path: str) -> Tuple[List[FunctionNode], List[ImportNode]]:
        """
        Parse a Python file and extract functions and imports.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Tuple of (functions, imports)
        """
        self.current_file = file_path
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code, filename=file_path)
            
            functions = self._extract_functions(tree, source_code)
            imports = self._extract_imports(tree)
            
            logger.info(f"Parsed {file_path}: {len(functions)} functions, {len(imports)} imports")
            return functions, imports
            
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return [], []
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return [], []
    
    def _extract_functions(self, tree: ast.AST, source_code: str) -> List[FunctionNode]:
        """Extract all function definitions from AST."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_node = self._parse_function(node, source_code)
                if func_node:
                    functions.append(func_node)
        
        return functions
    
    def _parse_function(self, node: ast.FunctionDef, source_code: str) -> Optional[FunctionNode]:
        """Parse a single function definition."""
        try:
            # Extract signature
            signature = self._get_function_signature(node)
            
            # Extract parameters
            parameters = [arg.arg for arg in node.args.args]
            
            # Extract return type
            return_type = None
            if node.returns:
                return_type = ast.unparse(node.returns)
            
            # Extract docstring
            docstring = ast.get_docstring(node)
            
            # Extract function calls
            calls = self._extract_function_calls(node)
            
            # Extract imports used (from function body)
            imports_used = self._extract_imports_from_calls(calls)
            
            # Get body preview (first 3 statements, textified)
            body_preview = self._textify_function_body(node, source_code)
            
            return FunctionNode(
                name=node.name,
                file_path=self.current_file,
                signature=signature,
                parameters=parameters,
                return_type=return_type,
                docstring=docstring,
                body_preview=body_preview,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                calls=list(calls),
                imports_used=imports_used
            )
            
        except Exception as e:
            logger.warning(f"Error parsing function {node.name}: {e}")
            return None
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Get function signature as string."""
        try:
            # Build parameter list
            params = []
            for arg in node.args.args:
                param_str = arg.arg
                if arg.annotation:
                    param_str += f": {ast.unparse(arg.annotation)}"
                params.append(param_str)
            
            # Add *args if present
            if node.args.vararg:
                vararg_str = f"*{node.args.vararg.arg}"
                if node.args.vararg.annotation:
                    vararg_str += f": {ast.unparse(node.args.vararg.annotation)}"
                params.append(vararg_str)
            
            # Add **kwargs if present
            if node.args.kwarg:
                kwarg_str = f"**{node.args.kwarg.arg}"
                if node.args.kwarg.annotation:
                    kwarg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
                params.append(kwarg_str)
            
            signature = f"{node.name}({', '.join(params)})"
            
            # Add return type
            if node.returns:
                signature += f" -> {ast.unparse(node.returns)}"
            
            return signature
            
        except Exception as e:
            logger.warning(f"Error building signature for {node.name}: {e}")
            return f"{node.name}(...)"
    
    def _extract_function_calls(self, node: ast.FunctionDef) -> Set[str]:
        """Extract all function calls within a function."""
        calls = set()
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_call_name(child.func)
                if call_name:
                    calls.add(call_name)
        
        return calls
    
    def _get_call_name(self, node: ast.AST) -> Optional[str]:
        """Get the name of a called function."""
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
    
    def _extract_imports_from_calls(self, calls: Set[str]) -> List[str]:
        """Extract module names from function calls."""
        imports = []
        for call in calls:
            if '.' in call:
                # Extract module name from qualified calls
                module = call.split('.')[0]
                imports.append(module)
        return list(set(imports))
    
    def _textify_function_body(self, node: ast.FunctionDef, source_code: str) -> str:
        """
        Create textified representation of function body.
        Takes first 3 executable statements and normalizes them.
        """
        try:
            statements = []
            count = 0
            max_statements = 3
            
            for stmt in node.body:
                # Skip docstrings
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, (ast.Str, ast.Constant)):
                    continue
                
                if count >= max_statements:
                    break
                
                # Get statement text and normalize
                stmt_text = ast.unparse(stmt)
                normalized = self._normalize_statement(stmt_text)
                statements.append(normalized)
                count += 1
            
            return " | ".join(statements)
            
        except Exception as e:
            logger.warning(f"Error textifying function body: {e}")
            return ""
    
    def _normalize_statement(self, stmt: str) -> str:
        """
        Normalize a statement by replacing variable names with placeholders.
        Keeps function names and keywords.
        """
        # Replace string literals
        stmt = re.sub(r'"[^"]*"', '"STR"', stmt)
        stmt = re.sub(r"'[^']*'", "'STR'", stmt)
        
        # Replace numbers
        stmt = re.sub(r'\b\d+\.?\d*\b', 'NUM', stmt)
        
        # Replace variable names (simple heuristic)
        # Keep common keywords and function calls
        keywords = {'if', 'else', 'elif', 'for', 'while', 'return', 'yield', 'with', 'as', 'in', 'not', 'and', 'or'}
        
        # This is a simplified normalization
        # In production, you'd want more sophisticated variable detection
        
        return stmt.strip()
    
    def _extract_imports(self, tree: ast.AST) -> List[ImportNode]:
        """Extract all import statements from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportNode(
                        module=alias.name,
                        names=[alias.name],
                        alias=alias.asname,
                        line_number=node.lineno,
                        is_from_import=False
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [alias.name for alias in node.names]
                    imports.append(ImportNode(
                        module=node.module,
                        names=names,
                        alias=None,
                        line_number=node.lineno,
                        is_from_import=True
                    ))
        
        return imports
    
    def extract_function_calls_from_code(self, code: str) -> Set[str]:
        """
        Extract function calls from a code snippet.
        Used for analyzing generated code.
        
        Args:
            code: Python code string
            
        Returns:
            Set of function names called
        """
        try:
            tree = ast.parse(code)
            calls = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    call_name = self._get_call_name(node.func)
                    if call_name:
                        calls.add(call_name)
            
            return calls
            
        except Exception as e:
            logger.error(f"Error extracting calls from code: {e}")
            return set()
    
    def extract_imports_from_code(self, code: str) -> List[ImportNode]:
        """
        Extract imports from a code snippet.
        
        Args:
            code: Python code string
            
        Returns:
            List of ImportNode objects
        """
        try:
            tree = ast.parse(code)
            return self._extract_imports(tree)
        except Exception as e:
            logger.error(f"Error extracting imports from code: {e}")
            return []
    
    def get_function_by_name(self, file_path: str, function_name: str) -> Optional[FunctionNode]:
        """
        Get a specific function from a file by name.
        
        Args:
            file_path: Path to Python file
            function_name: Name of function to find
            
        Returns:
            FunctionNode if found, None otherwise
        """
        functions, _ = self.parse_file(file_path)
        
        for func in functions:
            if func.name == function_name:
                return func
        
        return None

# Made with Bob
