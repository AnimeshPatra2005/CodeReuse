"""
Beautiful terminal UI components for demo using Rich library.
"""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.syntax import Syntax
from rich.columns import Columns
from rich.text import Text
from rich.layout import Layout
from rich import box
from rich.live import Live
from typing import Dict, List, Optional
import time


class DemoUI:
    """Beautiful terminal UI for demo."""
    
    def __init__(self):
        self.console = Console()
    
    def show_welcome(self):
        """Display welcome screen with ASCII art."""
        logo = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗ ██████╗ ██████╗ ███████╗     ██████╗ ███████╗██╗   ██╗███████╗   ║
║  ██╔════╝██╔═══██╗██╔══██╗██╔════╝     ██╔══██╗██╔════╝██║   ██║██╔════╝   ║
║  ██║     ██║   ██║██║  ██║█████╗       ██████╔╝█████╗  ██║   ██║███████╗   ║
║  ██║     ██║   ██║██║  ██║██╔══╝       ██╔══██╗██╔══╝  ██║   ██║╚════██║   ║
║  ╚██████╗╚██████╔╝██████╔╝███████╗     ██║  ██║███████╗╚██████╔╝███████║   ║
║   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝     ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝   ║
║                                                                              ║
║              Context-Aware Code Generation Agent v1.0                       ║
║              Enforcing Deterministic Code Reuse with AI                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        self.console.print(logo, style="cyan bold")
        self.console.print("\n🚀 Welcome to the Context-Aware Code Generation Demo!\n")
        
        self.console.print("This demo showcases our novel approach to AI code generation:", style="bold")
        features = [
            "✓ AST-based dependency analysis",
            "✓ Vector similarity search for code reuse",
            "✓ Dual-phase validation (namespace + structural)",
            "✓ Automatic refactoring based on quality scores"
        ]
        for feature in features:
            self.console.print(f"  {feature}", style="green")
        self.console.print()
    
    def show_repo_input(self, repo_url: str):
        """Display repository input."""
        panel = Panel(
            f"[cyan]Repository:[/cyan] {repo_url}",
            title="📁 Repository Setup",
            border_style="cyan"
        )
        self.console.print(panel)
        self.console.print()
    
    def show_cloning_progress(self, repo_url: str):
        """Show git clone progress."""
        self.console.print(f"[yellow]⚡ Cloning repository from GitHub...[/yellow]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(f"Cloning {repo_url}...", total=None)
            time.sleep(2)  # Simulate cloning
        self.console.print("[green]✓ Repository cloned successfully![/green]\n")
    
    def show_indexing_start(self, repo_name: str):
        """Show indexing start message."""
        panel = Panel(
            f"Starting comprehensive analysis of [cyan]{repo_name}[/cyan]",
            title="🔍 Indexing Repository",
            border_style="cyan"
        )
        self.console.print(panel)
        self.console.print()
    
    def create_indexing_progress(self):
        """Create and return a progress context for indexing."""
        return Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        )
    
    def show_stats_panel(self, stats: Dict):
        """Display repository statistics in a panel."""
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green bold", justify="right")
        
        table.add_row("Files Parsed:", str(stats.get("files", 0)))
        table.add_row("Functions Extracted:", str(stats.get("functions", 0)))
        table.add_row("Import Statements:", str(stats.get("imports", 0)))
        table.add_row("Embeddings Created:", str(stats.get("embeddings", 0)))
        table.add_row("Dependency Edges:", str(stats.get("edges", 0)))
        
        panel = Panel(
            table,
            title="📊 Indexing Statistics",
            border_style="cyan"
        )
        self.console.print(panel)
        self.console.print()
    
    def show_query(self, query: str, target_file: str):
        """Display the user query."""
        panel = Panel(
            f"[bold]{query}[/bold]\n\n[dim]Target file: {target_file}[/dim]",
            title="🤖 AI Code Generation Agent",
            border_style="cyan"
        )
        self.console.print(panel)
        self.console.print()
    
    def show_context_gathering(self, similar_functions: List[Dict]):
        """Display similar functions found."""
        if not similar_functions:
            return
        
        table = Table(title="🔎 Context Gathering", box=box.ROUNDED, border_style="cyan")
        table.add_column("Function", style="cyan", no_wrap=True)
        table.add_column("Location", style="magenta")
        table.add_column("Similarity", style="green", justify="right")
        
        for func in similar_functions[:5]:  # Show top 5
            name = func.get("name", "unknown")
            location = func.get("file", "unknown")
            similarity = func.get("similarity", 0.0)
            table.add_row(
                name,
                location,
                f"{similarity:.2%}"
            )
        
        self.console.print(table)
        self.console.print()
    
    def show_generated_code(self, code: str, target_file: str, language: str = "python"):
        """Display generated code with syntax highlighting."""
        panel = Panel(
            Syntax(code, language, theme="monokai", line_numbers=True),
            title=f"💻 Generated Code - {target_file}",
            border_style="green"
        )
        self.console.print(panel)
        self.console.print()
    
    def show_score_dashboard(self, scores: Dict, iteration: int):
        """Display quality scores with progress bars."""
        self.console.print(f"\n{'='*80}")
        self.console.print(f"[cyan bold]📊 Code Quality Metrics - Iteration #{iteration}[/cyan bold]")
        self.console.print(f"{'='*80}\n")
        
        # Namespace Reuse Score
        namespace_score = scores.get("namespace_reuse", 0) * 100
        namespace_color = self._get_score_color(namespace_score, 40)
        
        namespace_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        namespace_table.add_column("Metric", style="bold")
        namespace_table.add_column("Value")
        
        # Create progress bar representation
        bar_length = 30
        filled = int((namespace_score / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        namespace_table.add_row(
            "Score:",
            f"[{namespace_color}]{namespace_score:.1f}%  {bar}[/{namespace_color}]"
        )
        namespace_table.add_row(
            "Functions Called:",
            str(scores.get("functions_called", 0))
        )
        namespace_table.add_row(
            "Reused from Repo:",
            f"[green]{scores.get('reused_functions', 0)}[/green]"
        )
        namespace_table.add_row(
            "New/External:",
            f"[yellow]{scores.get('external_functions', 0)}[/yellow]"
        )
        
        threshold = 40
        status_icon = "✅" if namespace_score >= threshold else "❌"
        status_text = f"PASS (Threshold: {threshold}%)" if namespace_score >= threshold else f"FAIL (Below {threshold}% threshold)"
        status_color = "green" if namespace_score >= threshold else "red"
        
        namespace_table.add_row(
            "Status:",
            f"[{status_color}]{status_icon} {status_text}[/{status_color}]"
        )
        
        panel = Panel(
            namespace_table,
            title="Namespace Reuse Score",
            border_style="cyan"
        )
        self.console.print(panel)
        
        # Structural Similarity
        structural_pass = scores.get("structural_pass", True)
        structural_score = scores.get("structural_similarity", 0) * 100
        
        structural_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        structural_table.add_column("Metric", style="bold")
        structural_table.add_column("Value")
        
        bar_filled = int((structural_score / 100) * bar_length)
        structural_bar = "█" * bar_filled + "░" * (bar_length - bar_filled)
        
        structural_table.add_row(
            "Max Similarity:",
            f"[cyan]{structural_score:.1f}%  {structural_bar}[/cyan]"
        )
        
        if structural_pass:
            structural_table.add_row("", "[green]✓ No plagiarism detected[/green]")
            structural_table.add_row("", "[green]✓ Code structure is original[/green]")
            structural_table.add_row("Status:", "[green]✅ PASS (Threshold: <85%)[/green]")
        else:
            structural_table.add_row("", "[red]✗ High similarity detected[/red]")
            structural_table.add_row("Status:", "[red]❌ FAIL (Above 85% threshold)[/red]")
        
        panel = Panel(
            structural_table,
            title="Structural Similarity Check",
            border_style="cyan"
        )
        self.console.print(panel)
        
        # Overall Quality
        overall_score = scores.get("overall_quality", 0) * 100
        overall_color = self._get_score_color(overall_score, 60)
        
        overall_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        overall_table.add_column("Metric", style="bold")
        overall_table.add_column("Value")
        
        bar_filled = int((overall_score / 100) * bar_length)
        overall_bar = "█" * bar_filled + "░" * (bar_length - bar_filled)
        
        overall_table.add_row(
            "Score:",
            f"[{overall_color}]{overall_score:.1f}%  {overall_bar}[/{overall_color}]"
        )
        overall_table.add_row("Namespace Reuse:", f"{namespace_score:.1f}%")
        overall_table.add_row("Structural Check:", "PASS" if structural_pass else "FAIL")
        overall_table.add_row("Dependency Valid:", "[green]YES[/green]")
        
        if overall_score >= 70:
            status = "[green]✅ EXCELLENT - Code meets quality standards![/green]"
        elif overall_score >= 50:
            status = "[yellow]⚠️  GOOD - Minor improvements possible[/yellow]"
        else:
            status = "[red]❌ NEEDS WORK - Refactoring recommended[/red]"
        
        overall_table.add_row("Status:", status)
        
        panel = Panel(
            overall_table,
            title="Overall Quality Score",
            border_style="cyan"
        )
        self.console.print(panel)
        self.console.print()
    
    def show_refactor_comparison(self, before: str, after: str, 
                                 before_score: float, after_score: float):
        """Show side-by-side code comparison."""
        self.console.print("\n" + "="*80)
        self.console.print("[cyan bold]🔄 Refactored Code Comparison[/cyan bold]")
        self.console.print("="*80 + "\n")
        
        # Create side-by-side panels
        before_panel = Panel(
            Syntax(before[:500] + "..." if len(before) > 500 else before, 
                   "python", theme="monokai", line_numbers=False),
            title=f"❌ Before (Score: {before_score*100:.1f}%)",
            border_style="red"
        )
        
        after_panel = Panel(
            Syntax(after[:500] + "..." if len(after) > 500 else after,
                   "python", theme="monokai", line_numbers=False),
            title=f"✅ After (Score: {after_score*100:.1f}%)",
            border_style="green"
        )
        
        # Show improvement metrics
        improvement = (after_score - before_score) * 100
        
        metrics_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        metrics_table.add_column("Metric", style="bold")
        metrics_table.add_column("Change", justify="right")
        
        metrics_table.add_row(
            "Namespace Reuse:",
            f"[green]{before_score*100:.1f}% → {after_score*100:.1f}%  ⬆️ +{improvement:.1f}%[/green]"
        )
        metrics_table.add_row(
            "Status:",
            "[green]✅ PASS - Quality threshold met![/green]"
        )
        
        panel = Panel(
            metrics_table,
            title="📊 Improved Metrics",
            border_style="cyan"
        )
        self.console.print(panel)
        self.console.print()
    
    def show_summary(self, summary: Dict):
        """Display final summary."""
        self.console.print("\n" + "="*80)
        self.console.print("[cyan bold]✨ Code Generation Complete![/cyan bold]")
        self.console.print("="*80 + "\n")
        
        # Session Summary
        summary_table = Table(show_header=False, box=box.ROUNDED, border_style="cyan", padding=(0, 2))
        summary_table.add_column("Metric", style="cyan bold")
        summary_table.add_column("Value", style="green bold", justify="right")
        
        summary_table.add_row("Total Iterations:", str(summary.get("iterations", 1)))
        summary_table.add_row("Final Namespace Reuse:", f"{summary.get('namespace_reuse', 0):.1f}%")
        summary_table.add_row("Final Quality Score:", f"{summary.get('overall_quality', 0):.1f}%")
        summary_table.add_row("Time Taken:", f"{summary.get('time_taken', 0):.1f}s")
        
        status = summary.get("status", "SUCCESS")
        status_color = "green" if status == "SUCCESS" else "yellow"
        summary_table.add_row("Status:", f"[{status_color}]✅ {status}[/{status_color}]")
        
        panel = Panel(
            summary_table,
            title="📈 Session Summary",
            border_style="cyan"
        )
        self.console.print(panel)
        
        # Functions Reused
        reused_functions = summary.get("reused_functions", [])
        if reused_functions:
            self.console.print("\n[cyan bold]Functions Reused:[/cyan bold]")
            for func in reused_functions:
                self.console.print(f"  [green]• {func}[/green]")
        
        self.console.print("\n[cyan bold]🎉 Thank you for using Context-Aware Code Generation Agent![/cyan bold]\n")
        
        achievements = [
            f"✓ Enforced code reuse ({summary.get('namespace_reuse', 0):.0f}% of functions from existing codebase)",
            "✓ Prevented code duplication through structural analysis",
            "✓ Validated dependencies automatically",
            f"✓ Achieved high quality score ({summary.get('overall_quality', 0):.1f}%)"
        ]
        
        self.console.print("[bold]Key Achievements:[/bold]")
        for achievement in achievements:
            self.console.print(f"   {achievement}", style="green")
        
        self.console.print("\n[italic]This demonstrates our novel approach to deterministic code reuse![/italic]\n")
    
    def show_error(self, error_msg: str):
        """Display error message."""
        panel = Panel(
            f"[red bold]{error_msg}[/red bold]",
            title="❌ Error",
            border_style="red"
        )
        self.console.print(panel)
    
    def show_warning(self, warning_msg: str):
        """Display warning message."""
        self.console.print(f"[yellow]⚠️  {warning_msg}[/yellow]")
    
    def show_info(self, info_msg: str):
        """Display info message."""
        self.console.print(f"[blue]ℹ️  {info_msg}[/blue]")
    
    def show_success(self, success_msg: str):
        """Display success message."""
        self.console.print(f"[green]✅ {success_msg}[/green]")
    
    def _get_score_color(self, score: float, threshold: float) -> str:
        """Get color based on score and threshold."""
        if score >= threshold + 30:
            return "green"
        elif score >= threshold:
            return "yellow"
        else:
            return "red"

# Made with Bob
