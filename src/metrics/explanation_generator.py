"""
Explanation Generator - Generates human-readable explanations for validation failures.
"""

from typing import List
from src.models.data_models import (
    MetricResult, NamespaceResult, StructuralResult, 
    DependencyResult, FunctionNode
)
from src.indexing.vector_db import VectorDBManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExplanationGenerator:
    """Generate explanations for validation failures to guide the agent."""
    
    def __init__(self, vector_db: VectorDBManager):
        """
        Initialize Explanation Generator.
        
        Args:
            vector_db: Vector database manager
        """
        self.vector_db = vector_db
    
    def generate_explanation(self, metric_result: MetricResult, user_request: str) -> str:
        """
        Generate comprehensive explanation for validation failure.
        
        Args:
            metric_result: Metric validation result
            user_request: Original user request
            
        Returns:
            Detailed explanation string
        """
        logger.info("Generating validation failure explanation...")
        
        explanation_parts = []
        
        # Header
        explanation_parts.append("=" * 80)
        explanation_parts.append("CODE VALIDATION FAILED")
        explanation_parts.append("=" * 80)
        explanation_parts.append("")
        
        # Summary
        explanation_parts.append("SUMMARY:")
        explanation_parts.append(metric_result.get_failure_summary())
        explanation_parts.append("")
        
        # Namespace failures
        if metric_result.namespace_result and not metric_result.namespace_result.passed:
            explanation_parts.append(self._explain_namespace_failure(
                metric_result.namespace_result,
                user_request
            ))
        
        # Structural failures
        if metric_result.structural_result and not metric_result.structural_result.passed:
            explanation_parts.append(self._explain_structural_failure(
                metric_result.structural_result
            ))
        
        # Dependency failures
        if metric_result.dependency_result and not metric_result.dependency_result.passed:
            explanation_parts.append(self._explain_dependency_failure(
                metric_result.dependency_result
            ))
        
        # General guidance
        explanation_parts.append(self._generate_general_guidance())
        
        # Footer
        explanation_parts.append("=" * 80)
        explanation_parts.append(f"Retry attempt: {metric_result.retry_count + 1}")
        explanation_parts.append("=" * 80)
        
        return "\n".join(explanation_parts)
    
    def _explain_namespace_failure(
        self,
        namespace_result: NamespaceResult,
        user_request: str
    ) -> str:
        """Generate explanation for namespace check failure."""
        
        explanation = []
        explanation.append("NAMESPACE REUSE FAILURE:")
        explanation.append("-" * 80)
        explanation.append("")
        
        # Explain the issue
        reuse_pct = namespace_result.reuse_score * 100
        required_pct = 40  # From config
        
        explanation.append(f"Your code only reuses {reuse_pct:.1f}% of existing functions.")
        explanation.append(f"Minimum required: {required_pct}%")
        explanation.append("")
        
        # Show what was called
        if namespace_result.called_functions:
            explanation.append(f"Functions you called ({len(namespace_result.called_functions)}):")
            for func in sorted(namespace_result.called_functions):
                is_repo = func in namespace_result.repo_functions_used
                marker = "✓" if is_repo else "✗"
                explanation.append(f"  {marker} {func}")
            explanation.append("")
        
        # Suggest alternatives
        explanation.append("SUGGESTED FIXES:")
        explanation.append("")
        
        # Find relevant functions to reuse
        suggestions = self._find_reusable_functions(user_request)
        
        if suggestions:
            explanation.append("Consider using these existing functions:")
            for func in suggestions[:5]:  # Top 5
                explanation.append(f"  • {func.name} - {func.signature}")
                if func.docstring:
                    explanation.append(f"    {func.docstring[:100]}...")
                explanation.append(f"    File: {func.file_path}")
                explanation.append("")
        
        explanation.append("IMPORTANT:")
        explanation.append("  1. Import existing functions at the top of your code")
        explanation.append("  2. Call them instead of reimplementing their logic")
        explanation.append("  3. Do NOT copy-paste their implementation")
        explanation.append("")
        
        return "\n".join(explanation)
    
    def _explain_structural_failure(self, structural_result: StructuralResult) -> str:
        """Generate explanation for structural similarity failure."""
        
        explanation = []
        explanation.append("STRUCTURAL PLAGIARISM DETECTED:")
        explanation.append("-" * 80)
        explanation.append("")
        
        explanation.append("Your code has high structural similarity with existing functions.")
        explanation.append("This suggests you copied the logic instead of calling the function.")
        explanation.append("")
        
        # Show violations
        for i, violation in enumerate(structural_result.violations, 1):
            explanation.append(f"Violation {i}:")
            explanation.append(f"  Your function: {violation.generated_function}")
            explanation.append(f"  Similar to: {violation.similar_repo_function}")
            explanation.append(f"  Similarity: {violation.similarity_score:.1%}")
            explanation.append(f"  Location: {violation.repo_file_path}")
            explanation.append("")
            explanation.append(f"  {violation.explanation}")
            explanation.append("")
        
        explanation.append("HOW TO FIX:")
        explanation.append("  1. Import the existing function")
        explanation.append("  2. Call it directly instead of reimplementing")
        explanation.append("  3. If you need different behavior, wrap it or extend it")
        explanation.append("")
        
        explanation.append("Example:")
        if structural_result.violations:
            v = structural_result.violations[0]
            explanation.append(f"  # Instead of reimplementing {v.generated_function}:")
            explanation.append(f"  from {v.repo_file_path.replace('/', '.').replace('.py', '')} import {v.similar_repo_function}")
            explanation.append(f"  result = {v.similar_repo_function}(args)")
        explanation.append("")
        
        return "\n".join(explanation)
    
    def _explain_dependency_failure(self, dependency_result: DependencyResult) -> str:
        """Generate explanation for dependency validation failure."""
        
        explanation = []
        explanation.append("DEPENDENCY BREAKING CHANGES:")
        explanation.append("-" * 80)
        explanation.append("")
        
        explanation.append("Your changes would break existing code that depends on this file.")
        explanation.append("")
        
        # Show breaking changes
        for i, change in enumerate(dependency_result.breaking_changes, 1):
            explanation.append(f"Breaking Change {i}:")
            explanation.append(f"  Affected file: {change.affected_file}")
            explanation.append(f"  Affected function: {change.affected_function}")
            explanation.append(f"  Issue: {change.issue}")
            explanation.append(f"  Suggestion: {change.suggestion}")
            explanation.append("")
        
        explanation.append("HOW TO FIX:")
        explanation.append("  1. Maintain backward compatibility")
        explanation.append("  2. Add new parameters with default values")
        explanation.append("  3. Don't remove or rename existing functions")
        explanation.append("  4. Consider deprecation warnings for major changes")
        explanation.append("")
        
        return "\n".join(explanation)
    
    def _generate_general_guidance(self) -> str:
        """Generate general guidance for fixing validation failures."""
        
        guidance = []
        guidance.append("GENERAL GUIDANCE:")
        guidance.append("-" * 80)
        guidance.append("")
        guidance.append("Best Practices for Code Reuse:")
        guidance.append("")
        guidance.append("1. SEARCH FIRST:")
        guidance.append("   - Look at the 'SIMILAR EXISTING FUNCTIONS' provided")
        guidance.append("   - Check if any match your needs")
        guidance.append("")
        guidance.append("2. IMPORT AND CALL:")
        guidance.append("   - Add proper import statements")
        guidance.append("   - Call existing functions directly")
        guidance.append("   - Example: from module import function")
        guidance.append("")
        guidance.append("3. COMPOSE, DON'T COPY:")
        guidance.append("   - Build new functionality by combining existing functions")
        guidance.append("   - Add thin wrappers if needed")
        guidance.append("   - Don't duplicate logic")
        guidance.append("")
        guidance.append("4. WHEN TO CREATE NEW:")
        guidance.append("   - Only if no existing function matches")
        guidance.append("   - Keep it simple and focused")
        guidance.append("   - Still reuse utilities where possible")
        guidance.append("")
        
        return "\n".join(guidance)
    
    def _find_reusable_functions(self, query: str) -> List[FunctionNode]:
        """
        Find functions that could be reused for the given query.
        
        Args:
            query: Search query
            
        Returns:
            List of relevant FunctionNode objects
        """
        results = self.vector_db.search_similar(
            query=query,
            top_k=10,
            min_similarity=0.6,
            dynamic_k=True
        )
        
        return [result.function for result in results]
    
    def generate_success_message(self, metric_result: MetricResult) -> str:
        """
        Generate success message when validation passes.
        
        Args:
            metric_result: Metric validation result
            
        Returns:
            Success message
        """
        message = []
        message.append("=" * 80)
        message.append("✓ CODE VALIDATION PASSED")
        message.append("=" * 80)
        message.append("")
        
        if metric_result.namespace_result:
            reuse_pct = metric_result.namespace_result.reuse_score * 100
            message.append(f"Code Reuse Score: {reuse_pct:.1f}%")
            message.append(f"Repository Functions Used: {len(metric_result.namespace_result.repo_functions_used)}")
        
        if metric_result.structural_result:
            message.append(f"Max Structural Similarity: {metric_result.structural_result.max_similarity:.1%}")
        
        message.append("")
        message.append("Your code successfully reuses existing functionality!")
        message.append("=" * 80)
        
        return "\n".join(message)

# Made with Bob
