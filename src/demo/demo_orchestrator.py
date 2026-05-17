"""
Demo orchestrator that handles the complete workflow including GitHub cloning.
"""

import time
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, List
from urllib.parse import urlparse

from src.indexing.indexer import Indexer
from src.agent.agent_simple import SimpleAgent
from src.metrics.metric import MetricOrchestrator
from src.utils.config import load_config
from src.utils.logger import get_logger
from src.demo.ui_components import DemoUI

logger = get_logger(__name__)


class DemoOrchestrator:
    """Orchestrates the demo workflow with GitHub integration."""
    
    def __init__(self, repo_input: str, api_key: str):
        """
        Initialize the orchestrator.
        
        Args:
            repo_input: GitHub URL or local repository path
            api_key: Gemini API key
        """
        self.repo_input = repo_input
        self.api_key = api_key
        self.config = load_config()
        self.ui = DemoUI()
        
        self.repo_path: Optional[str] = None
        self.is_cloned = False
        self.temp_dir: Optional[str] = None
        
        self.indexer: Optional[Indexer] = None
        self.agent: Optional[SimpleAgent] = None
        self.metric_orchestrator: Optional[MetricOrchestrator] = None
    
    def _is_github_url(self, input_str: str) -> bool:
        """Check if input is a GitHub URL."""
        try:
            parsed = urlparse(input_str)
            return parsed.netloc in ['github.com', 'www.github.com'] and parsed.scheme in ['http', 'https']
        except:
            return False
    
    def _clone_repository(self, github_url: str) -> str:
        """
        Clone a GitHub repository to a temporary directory.
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            Path to cloned repository
        """
        self.ui.show_cloning_progress(github_url)
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="demo_repo_")
        
        try:
            # Clone the repository
            result = subprocess.run(
                ['git', 'clone', github_url, self.temp_dir],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            self.is_cloned = True
            logger.info(f"Repository cloned to {self.temp_dir}")
            return self.temp_dir
            
        except subprocess.TimeoutExpired:
            raise Exception("Repository cloning timed out (5 minutes)")
        except FileNotFoundError:
            raise Exception("Git is not installed or not in PATH")
        except Exception as e:
            # Clean up on failure
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    def _prepare_repository(self) -> str:
        """
        Prepare repository - clone if URL, validate if local path.
        
        Returns:
            Path to repository
        """
        if self._is_github_url(self.repo_input):
            self.ui.show_info("Detected GitHub URL")
            return self._clone_repository(self.repo_input)
        else:
            # Local path
            if not os.path.exists(self.repo_input):
                raise Exception(f"Local repository path does not exist: {self.repo_input}")
            
            if not os.path.isdir(self.repo_input):
                raise Exception(f"Path is not a directory: {self.repo_input}")
            
            self.ui.show_success(f"Using local repository: {self.repo_input}")
            return self.repo_input
    
    def run_demo(self, user_query: str, target_file: str, 
                 mode: str = "legacy", max_iterations: int = 3):
        """
        Run the complete demo workflow.
        
        Args:
            user_query: Code generation request
            target_file: Target file for code generation
            mode: Agent mode (legacy/greenfield)
            max_iterations: Maximum refactor iterations
            
        Returns:
            Tuple of (generated_code, scores)
        """
        start_time = time.time()
        
        try:
            # 1. Welcome screen
            self.ui.show_welcome()
            time.sleep(1)
            
            # 2. Show repository input
            self.ui.show_repo_input(self.repo_input)
            
            # 3. Prepare repository (clone if needed)
            self.repo_path = self._prepare_repository()
            
            # 4. Index repository
            self._index_repository()
            
            # 5. Show query
            self.ui.show_query(user_query, target_file)
            time.sleep(1)
            
            # 6. Generate code with iterations
            final_code, final_scores = self._generate_with_iterations(
                user_query, target_file, mode, max_iterations
            )
            
            # 7. Show final summary
            elapsed_time = time.time() - start_time
            self._show_final_summary(final_code, final_scores, elapsed_time)
            
            return final_code, final_scores
            
        except Exception as e:
            logger.error(f"Demo error: {e}")
            self.ui.show_error(str(e))
            raise
        finally:
            # Cleanup cloned repository
            self._cleanup()
    
    def _index_repository(self):
        """Index repository with progress display."""
        repo_name = os.path.basename(self.repo_path)
        self.ui.show_indexing_start(repo_name)
        
        # Create indexer
        self.indexer = Indexer(
            repository_path=self.repo_path,
            exclude_patterns=self.config.repository.exclude_patterns
        )
        
        # Index with progress display
        start_time = time.time()
        
        # Simplified progress display - single spinner for all phases
        with self.ui.create_indexing_progress() as progress:
            task = progress.add_task(
                "[cyan]Analyzing repository (AST parsing, dependency graph, embeddings)...",
                total=100
            )
            
            # Run indexing - all phases happen internally
            metadata = self.indexer.index_repository()
            
            # Mark as complete (100%)
            progress.update(task, completed=100)
        
        elapsed = time.time() - start_time
        
        # Show statistics
        stats = {
            "files": metadata.total_files,
            "functions": metadata.total_functions,
            "imports": metadata.total_imports,
            "embeddings": metadata.total_functions,
            "edges": len(self.indexer.graph_builder.call_graph) if hasattr(self.indexer.graph_builder, 'call_graph') else 0
        }
        self.ui.show_stats_panel(stats)
        
        # Initialize metric orchestrator FIRST so it can be injected into agent
        self.metric_orchestrator = MetricOrchestrator(
            self.indexer.vector_db,
            self.indexer.graph_builder
        )
        
        # Initialize agent — Bug #2 fix: pass repo_path; Bug #4 fix: pass metric_orchestrator
        self.agent = SimpleAgent(
            self.indexer.vector_db,
            self.indexer.graph_builder,
            self.api_key,
            repo_path=self.repo_path,
            metrics_orchestrator=self.metric_orchestrator
        )
        
        self.ui.show_success(f"Indexing complete in {elapsed:.1f}s")
    
    def _generate_with_iterations(self, query: str, target_file: str,
                                  mode: str, max_iterations: int):
        """Generate code with automatic refactoring."""
        iteration = 1
        previous_code = None
        previous_scores = None
        
        while iteration <= max_iterations:
            self.ui.console.print(f"\n{'='*80}")
            self.ui.console.print(f"[cyan bold]Iteration #{iteration}[/cyan bold]")
            self.ui.console.print(f"{'='*80}\n")
            
            # Generate code
            self.ui.show_info("Agent is thinking...")
            response = self.agent.generate_code_simple(query, target_file, mode)
            generated_code = response.get("code", "")
            
            # Bug #1 fix: treat empty code as a hard failure — do NOT score it
            if not generated_code or not generated_code.strip():
                self.ui.show_warning(
                    "Code generation produced empty output (LLM returned no code). "
                    "Check HUGGINGFACE_API_TOKEN and model availability."
                )
                if iteration >= max_iterations:
                    self.ui.show_warning(f"Max iterations ({max_iterations}) reached with no output")
                    return "", {
                        "namespace_reuse": 0.0,
                        "structural_pass": True,
                        "structural_similarity": 0.0,
                        "overall_quality": 0.0,
                        "functions_called": 0,
                        "reused_functions": 0,
                        "external_functions": 0
                    }
                iteration += 1
                time.sleep(2)
                continue
            
            # Show generated code
            self.ui.show_generated_code(generated_code, target_file)
            
            # Calculate scores
            scores = self._calculate_scores(generated_code, target_file)
            
            # Show score dashboard
            self.ui.show_score_dashboard(scores, iteration)
            
            # Check if refactor needed
            namespace_score = scores.get("namespace_reuse", 0)
            threshold = self.config.metrics.namespace.min_reuse_score
            
            if namespace_score >= threshold or iteration >= max_iterations:
                # Success or max iterations reached
                if namespace_score >= threshold:
                    self.ui.show_success("Quality threshold met!")
                else:
                    self.ui.show_warning(f"Max iterations ({max_iterations}) reached")
                return generated_code, scores
            
            # Show refactor comparison if we have previous code
            if previous_code:
                self.ui.show_refactor_comparison(
                    previous_code, generated_code,
                    previous_scores.get("namespace_reuse", 0),
                    scores.get("namespace_reuse", 0)
                )
            
            # Prepare for next iteration
            previous_code = generated_code
            previous_scores = scores
            iteration += 1
            
            self.ui.show_warning("Initiating automatic refactor...")
            time.sleep(2)
        
        return generated_code, scores
    
    def _calculate_scores(self, code: str, target_file: str) -> Dict:
        """Calculate quality scores."""
        try:
            # Use metric orchestrator with correct parameters
            from src.models.data_models import AgentMode
            result = self.metric_orchestrator.validate(
                generated_code=code,
                target_file=target_file,
                mode=AgentMode.LEGACY
            )
            
            # Safely extract scores with proper null checks
            namespace_score = 0.0
            structural_pass = True
            structural_similarity = 0.0
            functions_called = 0
            reused_functions = 0
            external_functions = 0
            
            if result.namespace_result:
                namespace_score = result.namespace_result.reuse_score
                if hasattr(result.namespace_result, 'called_functions'):
                    functions_called = len(result.namespace_result.called_functions)
                if hasattr(result.namespace_result, 'repo_functions_used'):
                    reused_functions = len(result.namespace_result.repo_functions_used)
                if hasattr(result.namespace_result, 'external_functions'):
                    external_functions = len(result.namespace_result.external_functions)
            
            if result.structural_result:
                structural_pass = result.structural_result.passed
                if hasattr(result.structural_result, 'max_similarity'):
                    structural_similarity = result.structural_result.max_similarity
            
            return {
                "namespace_reuse": namespace_score,
                "structural_pass": structural_pass,
                "structural_similarity": structural_similarity,
                "overall_quality": self._calculate_overall_score(result),
                "functions_called": functions_called,
                "reused_functions": reused_functions,
                "external_functions": external_functions
            }
        except Exception as e:
            logger.error(f"Error calculating scores: {e}")
            # Return default scores on error
            return {
                "namespace_reuse": 0.0,
                "structural_pass": True,
                "structural_similarity": 0.0,
                "overall_quality": 0.0,
                "functions_called": 0,
                "reused_functions": 0,
                "external_functions": 0
            }
    
    def _calculate_overall_score(self, result) -> float:
        """Calculate overall quality score.
        
        Bug #1 fix: safely handle None namespace_result / structural_result
        so empty generated code doesn't produce a misleading 100% score.
        """
        namespace_weight = 0.6
        structural_weight = 0.4

        if result.namespace_result is not None:
            namespace_score = result.namespace_result.reuse_score
        else:
            namespace_score = 0.0

        if result.structural_result is not None:
            structural_score = 1.0 if result.structural_result.passed else 0.5
        else:
            structural_score = 1.0  # no structural violations on empty code

        return (namespace_score * namespace_weight +
                structural_score * structural_weight)
    
    def _show_final_summary(self, code: str, scores: Dict, elapsed_time: float):
        """Show final summary."""
        summary = {
            "iterations": 1,  # TODO: Track actual iterations
            "namespace_reuse": scores.get("namespace_reuse", 0) * 100,
            "overall_quality": scores.get("overall_quality", 0) * 100,
            "time_taken": elapsed_time,
            "status": "SUCCESS" if scores.get("namespace_reuse", 0) >= 0.4 else "NEEDS_WORK",
            "reused_functions": []  # TODO: Extract from scores
        }
        self.ui.show_summary(summary)
    
    def _cleanup(self):
        """Clean up temporary resources."""
        if self.is_cloned and self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")

# Made with Bob
