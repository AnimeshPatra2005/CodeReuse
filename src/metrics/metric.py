"""
Metric Orchestrator - Coordinates all validation checks and retry logic.
"""

from src.models.data_models import MetricResult, AgentMode
from src.metrics.namespace_checker import NamespaceChecker
from src.metrics.structural_matcher import StructuralMatcher
from src.metrics.dependency_validator import DependencyValidator
from src.metrics.explanation_generator import ExplanationGenerator
from src.indexing.vector_db import VectorDBManager
from src.indexing.dependency_graph import DependencyGraphBuilder
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class MetricOrchestrator:
    """Orchestrate all metric validations with retry logic."""
    
    def __init__(
        self,
        vector_db: VectorDBManager,
        dependency_graph: DependencyGraphBuilder
    ):
        """
        Initialize Metric Orchestrator.
        
        Args:
            vector_db: Vector database manager
            dependency_graph: Dependency graph builder
        """
        self.vector_db = vector_db
        self.dependency_graph = dependency_graph
        
        # Load config
        config = get_config()
        self.metrics_config = config.metrics
        self.max_retries = self.metrics_config.retry.max_retries
        
        # Initialize validators
        self.namespace_checker = NamespaceChecker(vector_db)
        self.structural_matcher = StructuralMatcher(vector_db)
        self.dependency_validator = DependencyValidator(dependency_graph)
        self.explanation_generator = ExplanationGenerator(vector_db)
    
    def validate(
        self,
        generated_code: str,
        target_file: str,
        mode: AgentMode = AgentMode.LEGACY,
        retry_count: int = 0
    ) -> MetricResult:
        """
        Validate generated code against all metrics.
        
        Args:
            generated_code: Code to validate
            target_file: Target file path
            mode: Agent mode (legacy or greenfield)
            retry_count: Current retry attempt
            
        Returns:
            MetricResult with validation results
        """
        logger.info(f"Validating code (mode: {mode}, retry: {retry_count})...")
        
        # Greenfield mode: skip validation
        if mode == AgentMode.GREENFIELD:
            return MetricResult(
                passed=True,
                namespace_result=None,
                structural_result=None,
                dependency_result=None,
                explanation="Greenfield mode - validation skipped",
                retry_count=retry_count
            )
        
        # Legacy mode: full validation
        try:
            # Run all checks
            namespace_result = None
            structural_result = None
            dependency_result = None
            
            # 1. Namespace check
            if self.metrics_config.namespace.enabled:
                namespace_result = self.namespace_checker.check(
                    generated_code,
                    target_file
                )
                logger.info(f"Namespace check: {'PASSED' if namespace_result.passed else 'FAILED'}")
            
            # 2. Structural check
            if self.metrics_config.structural.enabled:
                structural_result = self.structural_matcher.check(
                    generated_code,
                    target_file
                )
                logger.info(f"Structural check: {'PASSED' if structural_result.passed else 'FAILED'}")
            
            # 3. Dependency check
            if self.metrics_config.dependency.enabled:
                dependency_result = self.dependency_validator.validate(
                    generated_code,
                    target_file
                )
                logger.info(f"Dependency check: {'PASSED' if dependency_result.passed else 'FAILED'}")
            
            # Determine overall pass/fail
            passed = self._determine_overall_result(
                namespace_result,
                structural_result,
                dependency_result
            )
            
            # Generate explanation if failed
            explanation = ""
            if not passed:
                metric_result_temp = MetricResult(
                    passed=False,
                    namespace_result=namespace_result,
                    structural_result=structural_result,
                    dependency_result=dependency_result,
                    explanation="",
                    retry_count=retry_count
                )
                explanation = self.explanation_generator.generate_explanation(
                    metric_result_temp,
                    ""  # User request would be passed from agent
                )
            else:
                metric_result_temp = MetricResult(
                    passed=True,
                    namespace_result=namespace_result,
                    structural_result=structural_result,
                    dependency_result=dependency_result,
                    explanation="",
                    retry_count=retry_count
                )
                explanation = self.explanation_generator.generate_success_message(
                    metric_result_temp
                )
            
            result = MetricResult(
                passed=passed,
                namespace_result=namespace_result,
                structural_result=structural_result,
                dependency_result=dependency_result,
                explanation=explanation,
                retry_count=retry_count
            )
            
            logger.info(f"Overall validation: {'PASSED' if passed else 'FAILED'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return MetricResult(
                passed=False,
                namespace_result=None,
                structural_result=None,
                dependency_result=None,
                explanation=f"Validation error: {e}",
                retry_count=retry_count
            )
    
    def _determine_overall_result(
        self,
        namespace_result,
        structural_result,
        dependency_result
    ) -> bool:
        """
        Determine overall pass/fail based on individual results.
        
        Args:
            namespace_result: Namespace check result
            structural_result: Structural check result
            dependency_result: Dependency check result
            
        Returns:
            True if all enabled checks passed
        """
        results = []
        
        if namespace_result is not None:
            results.append(namespace_result.passed)
        
        if structural_result is not None:
            results.append(structural_result.passed)
        
        if dependency_result is not None:
            results.append(dependency_result.passed)
        
        # All enabled checks must pass
        return all(results) if results else True
    
    def validate_with_retry(
        self,
        generated_code: str,
        target_file: str,
        mode: AgentMode = AgentMode.LEGACY,
        regenerate_callback=None
    ) -> MetricResult:
        """
        Validate with automatic retry logic.
        
        Args:
            generated_code: Initial generated code
            target_file: Target file path
            mode: Agent mode
            regenerate_callback: Function to call for regeneration
            
        Returns:
            Final MetricResult
        """
        if not self.metrics_config.retry.enabled or mode == AgentMode.GREENFIELD:
            return self.validate(generated_code, target_file, mode, 0)
        
        current_code = generated_code
        result = None
        
        for retry in range(self.max_retries + 1):
            result = self.validate(current_code, target_file, mode, retry)
            
            if result.passed:
                logger.info(f"Validation passed on attempt {retry + 1}")
                return result
            
            # If failed and retries remaining
            if retry < self.max_retries:
                logger.info(f"Validation failed, retrying ({retry + 1}/{self.max_retries})...")
                
                if regenerate_callback:
                    # Regenerate code with explanation
                    current_code = regenerate_callback(result.explanation)
                else:
                    # No callback, can't retry
                    logger.warning("No regenerate callback provided, cannot retry")
                    return result
            else:
                logger.warning(f"Validation failed after {self.max_retries} retries")
                return result
        
        # Should never reach here, but return last result as fallback
        return result if result else self.validate(generated_code, target_file, mode, 0)
    
    def get_validation_summary(self, result: MetricResult) -> dict:
        """
        Get a summary of validation results.
        
        Args:
            result: Metric result
            
        Returns:
            Dict with summary
        """
        summary = {
            'passed': result.passed,
            'retry_count': result.retry_count,
            'checks': {}
        }
        
        if result.namespace_result:
            summary['checks']['namespace'] = {
                'passed': result.namespace_result.passed,
                'reuse_score': result.namespace_result.reuse_score,
                'functions_used': len(result.namespace_result.repo_functions_used),
                'total_calls': len(result.namespace_result.called_functions)
            }
        
        if result.structural_result:
            summary['checks']['structural'] = {
                'passed': result.structural_result.passed,
                'max_similarity': result.structural_result.max_similarity,
                'violations': len(result.structural_result.violations)
            }
        
        if result.dependency_result:
            summary['checks']['dependency'] = {
                'passed': result.dependency_result.passed,
                'breaking_changes': len(result.dependency_result.breaking_changes),
                'warnings': len(result.dependency_result.warnings)
            }
        
        return summary
    
    def quick_check(self, generated_code: str) -> dict:
        """
        Perform a quick syntax and basic structure check.
        
        Args:
            generated_code: Code to check
            
        Returns:
            Dict with quick check results
        """
        import ast
        
        result = {
            'valid_syntax': False,
            'has_functions': False,
            'has_imports': False,
            'error': None
        }
        
        try:
            tree = ast.parse(generated_code)
            result['valid_syntax'] = True
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    result['has_functions'] = True
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    result['has_imports'] = True
            
        except SyntaxError as e:
            result['error'] = str(e)
        except Exception as e:
            result['error'] = str(e)
        
        return result

# Made with Bob
