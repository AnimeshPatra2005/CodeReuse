"""
LLM-based Dependent File Validator - Uses LLM to validate code compatibility.
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
from src.utils.granite_client import GraniteClient
from src.utils.logger import get_logger
from src.indexing.dependency_graph import DependencyGraphBuilder

logger = get_logger(__name__)


class LLMValidator:
    """Use LLM to validate generated code against dependent files."""
    
    def __init__(self, dependency_graph: DependencyGraphBuilder, api_key: Optional[str] = None):
        """
        Initialize LLM Validator.
        
        Args:
            dependency_graph: Dependency graph builder
            api_key: Hugging Face API token
        """
        self.dependency_graph = dependency_graph
        self.granite_client = GraniteClient(api_token=api_key)
    
    def validate_with_dependents(
        self,
        target_file: str,
        generated_code: str,
        max_dependents: int = 5
    ) -> Dict[str, Any]:
        """
        Validate generated code against dependent files using LLM.
        
        Args:
            target_file: Target file being modified
            generated_code: Generated code
            max_dependents: Maximum number of dependent files to check
            
        Returns:
            Dict with validation results
        """
        logger.info(f"Starting LLM validation for {target_file}")
        
        # Get dependent files
        dependent_files = self._get_dependent_files(target_file)
        
        if not dependent_files:
            logger.info("No dependent files found")
            return {
                'passed': True,
                'report': 'No dependent files to validate',
                'dependent_files': [],
                'issues': []
            }
        
        # Limit number of dependents to check
        dependent_files = dependent_files[:max_dependents]
        logger.info(f"Found {len(dependent_files)} dependent files to validate")
        
        # Read dependent file contents
        dependent_contents = self._read_dependent_files(dependent_files)
        
        # Build validation prompt
        prompt = self._build_validation_prompt(
            target_file,
            generated_code,
            dependent_contents
        )
        
        # Get LLM validation
        try:
            llm_response = self.granite_client.generate_with_retry(
                prompt=prompt,
                temperature=0.1,  # Low temperature for consistent validation
                max_tokens=500,
                max_retries=2
            )
            
            # Parse LLM response
            result = self._parse_llm_response(llm_response, dependent_files)
            
            logger.info(f"LLM validation complete: {result['report']}")
            return result
            
        except Exception as e:
            logger.error(f"Error during LLM validation: {e}")
            return {
                'passed': False,
                'report': f'Validation error: {str(e)}',
                'dependent_files': dependent_files,
                'issues': [f'LLM validation failed: {str(e)}']
            }
    
    def _get_dependent_files(self, target_file: str) -> List[str]:
        """Get files that depend on the target file."""
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
    
    def _read_dependent_files(self, file_paths: List[str]) -> Dict[str, str]:
        """Read contents of dependent files."""
        contents = {}
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        contents[file_path] = f.read()
                else:
                    logger.warning(f"Dependent file not found: {file_path}")
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        
        return contents
    
    def _build_validation_prompt(
        self,
        target_file: str,
        generated_code: str,
        dependent_contents: Dict[str, str]
    ) -> str:
        """Build prompt for LLM validation."""
        
        prompt = f"""You are a code compatibility validator. Analyze if the generated code will break any dependent files.

**Target File:** {target_file}

**Generated Code:**
```python
{generated_code}
```

**Dependent Files:**
"""
        
        for file_path, content in dependent_contents.items():
            # Truncate very long files
            truncated = content[:1000] + "..." if len(content) > 1000 else content
            prompt += f"\n\n**File: {file_path}**\n```python\n{truncated}\n```"
        
        prompt += """

**Task:**
1. Check if the generated code changes any function signatures that dependent files use
2. Check if any imports or dependencies are broken
3. Identify any compatibility issues

**Response Format:**
If NO issues found, respond with exactly: "No compatibility issues detected"
If issues found, list them clearly:
- Issue 1: [description]
- Issue 2: [description]

Your response:"""
        
        return prompt
    
    def _parse_llm_response(self, response: str, dependent_files: List[str]) -> Dict[str, Any]:
        """Parse LLM validation response."""
        
        response_lower = response.lower().strip()
        
        # Check for "no issues" variations
        no_issues_phrases = [
            'no compatibility issues',
            'no issues detected',
            'no problems found',
            'compatible',
            'no breaking changes'
        ]
        
        has_no_issues = any(phrase in response_lower for phrase in no_issues_phrases)
        
        if has_no_issues and '-' not in response:
            return {
                'passed': True,
                'report': 'No compatibility issues detected',
                'dependent_files': dependent_files,
                'issues': []
            }
        
        # Parse issues
        issues = []
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                issues.append(line.lstrip('-•').strip())
        
        return {
            'passed': len(issues) == 0,
            'report': response.strip(),
            'dependent_files': dependent_files,
            'issues': issues
        }


# Made with Bob