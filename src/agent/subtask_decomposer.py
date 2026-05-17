"""
Subtask Decomposer - Breaks down user requests into manageable subtasks using LLM.
"""

from typing import List, Optional
from src.models.data_models import Subtask, TaskDecomposition
from src.utils.granite_client import GraniteClient
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class SubtaskDecomposer:
    """Decompose complex tasks into smaller, manageable subtasks."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Subtask Decomposer.
        
        Args:
            api_key: Gemini API key (optional, can be set via env)
        """
        config = get_config()
        self.llm_config = config.agent.llm
        self.subtask_config = config.agent.subtask
        
        # Initialize Granite client instead of Gemini
        self.granite_client = GraniteClient(api_token=api_key)
    
    def decompose(self, user_request: str, target_file: str) -> TaskDecomposition:
        """
        Decompose user request into subtasks.
        
        Args:
            user_request: User's code generation request
            target_file: Target file for code generation
            
        Returns:
            TaskDecomposition with subtasks and reasoning
        """
        logger.info(f"Decomposing task: {user_request[:100]}...")
        
        prompt = self._build_decomposition_prompt(user_request, target_file)
        
        try:
            # Generate using Granite with retry
            response_text = self.granite_client.generate_with_retry(
                prompt=prompt,
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens,
                max_retries=3
            )
            
            # Parse response
            decomposition = self._parse_response(response_text)
            
            logger.info(f"Task decomposed into {len(decomposition.subtasks)} subtasks")
            return decomposition
            
        except Exception as e:
            logger.error(f"Error decomposing task: {e}")
            # Return fallback single subtask
            return TaskDecomposition(
                subtasks=[
                    Subtask(
                        id=1,
                        description=user_request,
                        estimated_complexity="medium"
                    )
                ],
                reasoning="Failed to decompose, using single task",
                estimated_total_time="unknown"
            )
    
    def _build_decomposition_prompt(self, user_request: str, target_file: str) -> str:
        """Build prompt for task decomposition."""
        return f"""You are an expert software architect. Break down the following code generation request into {self.subtask_config.min_subtasks}-{self.subtask_config.max_subtasks} independent, manageable subtasks.

**User Request:**
{user_request}

**Target File:**
{target_file}

**Requirements for Subtasks:**
1. Each subtask should be independently executable
2. Each subtask should have clear input/output
3. Each subtask should follow single responsibility principle
4. Subtasks should be ordered logically (dependencies first)
5. Each subtask should be specific and actionable

**Output Format (JSON):**
{{
  "reasoning": "Brief explanation of decomposition strategy",
  "estimated_total_time": "rough estimate (e.g., '30 minutes', '2 hours')",
  "subtasks": [
    {{
      "id": 1,
      "description": "Clear, specific description of what to implement",
      "estimated_complexity": "low|medium|high",
      "dependencies": []
    }},
    ...
  ]
}}

**Example:**
User Request: "Add email validation to user registration"
Output:
{{
  "reasoning": "Split into validation logic, integration, and error handling",
  "estimated_total_time": "45 minutes",
  "subtasks": [
    {{
      "id": 1,
      "description": "Create email validation function with regex pattern matching",
      "estimated_complexity": "low",
      "dependencies": []
    }},
    {{
      "id": 2,
      "description": "Integrate email validation into user registration flow",
      "estimated_complexity": "medium",
      "dependencies": [1]
    }},
    {{
      "id": 3,
      "description": "Add error handling and user feedback for invalid emails",
      "estimated_complexity": "low",
      "dependencies": [2]
    }}
  ]
}}

Now decompose the user request above. Return ONLY the JSON, no additional text.
"""
    
    def _parse_response(self, response_text: str) -> TaskDecomposition:
        """Parse LLM response into TaskDecomposition."""
        import json
        import re
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in response")
        
        # Parse JSON
        data = json.loads(json_str)
        
        # Create Subtask objects
        subtasks = []
        for st_data in data.get('subtasks', []):
            subtask = Subtask(
                id=st_data['id'],
                description=st_data['description'],
                estimated_complexity=st_data.get('estimated_complexity', 'medium'),
                dependencies=st_data.get('dependencies', [])
            )
            subtasks.append(subtask)
        
        # Validate subtask count
        if len(subtasks) < self.subtask_config.min_subtasks:
            logger.warning(f"Only {len(subtasks)} subtasks generated, minimum is {self.subtask_config.min_subtasks}")
        elif len(subtasks) > self.subtask_config.max_subtasks:
            logger.warning(f"Too many subtasks ({len(subtasks)}), truncating to {self.subtask_config.max_subtasks}")
            subtasks = subtasks[:self.subtask_config.max_subtasks]
        
        return TaskDecomposition(
            subtasks=subtasks,
            reasoning=data.get('reasoning', ''),
            estimated_total_time=data.get('estimated_total_time', 'unknown')
        )
    
    def validate_subtasks(self, subtasks: List[Subtask]) -> bool:
        """
        Validate that subtasks are well-formed.
        
        Args:
            subtasks: List of subtasks to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not subtasks:
            logger.error("No subtasks provided")
            return False
        
        # Check for duplicate IDs
        ids = [st.id for st in subtasks]
        if len(ids) != len(set(ids)):
            logger.error("Duplicate subtask IDs found")
            return False
        
        # Check dependencies are valid
        for subtask in subtasks:
            for dep_id in subtask.dependencies:
                if dep_id not in ids:
                    logger.error(f"Subtask {subtask.id} has invalid dependency: {dep_id}")
                    return False
                if dep_id >= subtask.id:
                    logger.error(f"Subtask {subtask.id} depends on later subtask {dep_id}")
                    return False
        
        return True
    
    def reorder_by_dependencies(self, subtasks: List[Subtask]) -> List[Subtask]:
        """
        Reorder subtasks based on dependencies (topological sort).
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            Reordered list of subtasks
        """
        # Simple topological sort
        ordered = []
        remaining = subtasks.copy()
        
        while remaining:
            # Find subtasks with no unmet dependencies
            ready = []
            for st in remaining:
                deps_met = all(
                    dep_id in [s.id for s in ordered]
                    for dep_id in st.dependencies
                )
                if deps_met:
                    ready.append(st)
            
            if not ready:
                # Circular dependency or invalid state
                logger.warning("Could not resolve all dependencies, using original order")
                return subtasks
            
            # Add ready subtasks to ordered list
            ordered.extend(ready)
            
            # Remove from remaining
            for st in ready:
                remaining.remove(st)
        
        return ordered

# Made with Bob
