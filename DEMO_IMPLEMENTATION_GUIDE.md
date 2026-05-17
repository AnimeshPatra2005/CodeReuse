# Enhanced CLI Demo - Implementation Guide

This guide provides complete instructions for implementing the beautiful terminal-based demo for the hackathon video.

## Overview

We'll create `demo.py` - an enhanced CLI that showcases the Context-Aware Code Generation Agent with:
- Beautiful terminal UI using the `rich` library
- Live indexing progress with statistics
- Interactive agent interface
- Real-time score visualization
- Automatic refactor loop with before/after comparison
- Professional summary output

## Prerequisites

### 1. Install Required Dependencies

Add to `requirements.txt`:
```
rich>=13.7.0
```

Install:
```bash
pip install rich
```

### 2. Verify Existing Components

Ensure these are working:
- ✅ `src/indexing/indexer.py` - Repository indexing
- ✅ `src/agent/agent.py` - Code generation
- ✅ `src/metrics/metric.py` - Quality scoring
- ✅ `src/utils/config.py` - Configuration
- ✅ `src/utils/logger.py` - Logging

## File Structure

```
ibmbob/
├── demo.py                          # Main demo script (NEW)
├── src/
│   └── demo/                        # Demo utilities (NEW)
│       ├── __init__.py
│       ├── ui_components.py         # Rich UI components
│       └── demo_orchestrator.py     # Demo workflow logic
├── DEMO_MOCKUP.md                   # Visual mockup (CREATED)
└── DEMO_IMPLEMENTATION_GUIDE.md     # This file (CREATED)
```

## Implementation Steps

### Step 1: Create UI Components Module

**File: `src/demo/ui_components.py`**

This module contains all the Rich UI components for beautiful terminal output.

**Key Components:**
1. `DemoUI` class with methods for:
   - Welcome screen with ASCII art
   - Progress bars for indexing
   - Statistics panels
   - Score visualization dashboards
   - Code comparison views
   - Summary reports

**Features to implement:**
- `show_welcome()` - ASCII art logo and intro
- `show_indexing_progress()` - Live progress bars
- `show_stats_panel()` - Repository statistics
- `show_context_gathering()` - Similar functions found
- `show_generated_code()` - Syntax-highlighted code
- `show_score_dashboard()` - Quality metrics with progress bars
- `show_refactor_comparison()` - Side-by-side before/after
- `show_summary()` - Final statistics

**Rich Components to Use:**
- `Panel` - Bordered boxes
- `Progress` - Progress bars
- `Table` - Data tables
- `Syntax` - Code highlighting
- `Console` - Main output
- `Live` - Real-time updates
- `Columns` - Side-by-side layout

### Step 2: Create Demo Orchestrator

**File: `src/demo/demo_orchestrator.py`**

This module orchestrates the demo workflow and integrates with existing components.

**Key Class: `DemoOrchestrator`**

**Methods:**
1. `run_demo()` - Main demo flow
2. `index_repository()` - Index with progress callbacks
3. `generate_code()` - Generate with streaming
4. `calculate_scores()` - Get quality metrics
5. `refactor_if_needed()` - Automatic refactor loop
6. `show_final_summary()` - Summary statistics

**Integration Points:**
- Use `Indexer` from `src/indexing/indexer.py`
- Use `Agent` from `src/agent/agent.py`
- Use `MetricOrchestrator` from `src/metrics/metric.py`
- Use `DemoUI` for all visual output

### Step 3: Create Main Demo Script

**File: `demo.py`**

Simple entry point that:
1. Loads configuration
2. Creates DemoOrchestrator
3. Runs the demo
4. Handles errors gracefully

**Command-line arguments:**
- `--repo` - Repository path or GitHub URL
- `--query` - Code generation request
- `--mode` - Agent mode (legacy/greenfield)
- `--no-refactor` - Skip automatic refactoring

## Detailed Implementation

### UI Components Implementation

```python
# src/demo/ui_components.py

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.syntax import Syntax
from rich.columns import Columns
from rich.text import Text
from rich.layout import Layout
from rich import box
from typing import Dict, List, Optional

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
        
        features = [
            "✓ AST-based dependency analysis",
            "✓ Vector similarity search for code reuse",
            "✓ Dual-phase validation (namespace + structural)",
            "✓ Automatic refactoring based on quality scores"
        ]
        for feature in features:
            self.console.print(f"  {feature}", style="green")
        self.console.print()
    
    def show_indexing_progress(self, phase: str, current: int, total: int):
        """Show indexing progress bar."""
        # Use Rich Progress with live updates
        pass
    
    def show_stats_panel(self, stats: Dict):
        """Display repository statistics in a panel."""
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green bold")
        
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
    
    def show_score_dashboard(self, scores: Dict, iteration: int):
        """Display quality scores with progress bars."""
        # Namespace Reuse Score
        namespace_score = scores.get("namespace_reuse", 0) * 100
        namespace_color = self._get_score_color(namespace_score, 40)
        
        # Create progress bar for namespace reuse
        # ... implementation
        
        # Structural Similarity
        # ... implementation
        
        # Overall Quality
        # ... implementation
    
    def show_refactor_comparison(self, before: str, after: str, 
                                 before_score: float, after_score: float):
        """Show side-by-side code comparison."""
        # Use Columns to show before/after
        # ... implementation
    
    def show_summary(self, summary: Dict):
        """Display final summary."""
        # ... implementation
    
    def _get_score_color(self, score: float, threshold: float) -> str:
        """Get color based on score and threshold."""
        if score >= threshold + 30:
            return "green"
        elif score >= threshold:
            return "yellow"
        else:
            return "red"
```

### Demo Orchestrator Implementation

```python
# src/demo/demo_orchestrator.py

import time
from pathlib import Path
from typing import Optional, Dict, List
import os

from src.indexing.indexer import Indexer
from src.agent.agent import Agent
from src.metrics.metric import MetricOrchestrator
from src.utils.config import load_config
from src.utils.logger import get_logger
from src.demo.ui_components import DemoUI

logger = get_logger(__name__)

class DemoOrchestrator:
    """Orchestrates the demo workflow."""
    
    def __init__(self, repo_path: str, api_key: str):
        self.repo_path = repo_path
        self.api_key = api_key
        self.config = load_config()
        self.ui = DemoUI()
        
        self.indexer: Optional[Indexer] = None
        self.agent: Optional[Agent] = None
        self.metric_orchestrator: Optional[MetricOrchestrator] = None
    
    def run_demo(self, user_query: str, target_file: str, 
                 mode: str = "legacy", max_iterations: int = 3):
        """Run the complete demo workflow."""
        try:
            # 1. Welcome screen
            self.ui.show_welcome()
            time.sleep(2)
            
            # 2. Repository input
            self.ui.console.print(f"\n📁 Repository: {self.repo_path}\n")
            time.sleep(1)
            
            # 3. Index repository
            self._index_repository()
            
            # 4. Show query
            self.ui.console.print(f"\n🤖 Query: {user_query}\n")
            time.sleep(1)
            
            # 5. Generate code with iterations
            final_code, final_scores = self._generate_with_iterations(
                user_query, target_file, mode, max_iterations
            )
            
            # 6. Show final summary
            self._show_final_summary(final_code, final_scores)
            
            return final_code, final_scores
            
        except Exception as e:
            logger.error(f"Demo error: {e}")
            self.ui.console.print(f"\n❌ Error: {e}", style="red bold")
            raise
    
    def _index_repository(self):
        """Index repository with progress display."""
        self.ui.console.print("🔍 Starting repository indexing...\n")
        
        # Create indexer
        self.indexer = Indexer(
            repository_path=self.repo_path,
            exclude_patterns=self.config.repository.exclude_patterns
        )
        
        # Index with progress callbacks
        # TODO: Add progress callbacks to Indexer
        start_time = time.time()
        metadata = self.indexer.index_repository()
        elapsed = time.time() - start_time
        
        # Show statistics
        stats = {
            "files": metadata.total_files,
            "functions": metadata.total_functions,
            "imports": metadata.total_imports,
            "embeddings": metadata.total_functions,
            "edges": len(self.indexer.graph_builder.call_graph)
        }
        self.ui.show_stats_panel(stats)
        
        # Initialize agent
        self.agent = Agent(
            self.indexer.vector_db,
            self.indexer.graph_builder,
            self.api_key
        )
        
        # Initialize metric orchestrator
        self.metric_orchestrator = MetricOrchestrator(
            self.indexer.graph_builder,
            self.indexer.vector_db
        )
        
        self.ui.console.print(f"\n✅ Indexing complete in {elapsed:.1f}s\n")
    
    def _generate_with_iterations(self, query: str, target_file: str,
                                  mode: str, max_iterations: int):
        """Generate code with automatic refactoring."""
        iteration = 1
        previous_code = None
        previous_scores = None
        
        while iteration <= max_iterations:
            self.ui.console.print(f"\n{'='*80}")
            self.ui.console.print(f"Iteration #{iteration}", style="cyan bold")
            self.ui.console.print(f"{'='*80}\n")
            
            # Generate code
            response = self.agent.generate_code_simple(query, target_file, mode)
            generated_code = response.get("code", "")
            
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
                    self.ui.console.print("\n✅ Quality threshold met!", 
                                        style="green bold")
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
            
            self.ui.console.print("\n⚠️  Initiating automatic refactor...\n",
                                style="yellow bold")
            time.sleep(2)
        
        return generated_code, scores
    
    def _calculate_scores(self, code: str, target_file: str) -> Dict:
        """Calculate quality scores."""
        # Use metric orchestrator
        result = self.metric_orchestrator.validate_code(
            code, target_file, self.repo_path
        )
        
        return {
            "namespace_reuse": result.namespace_result.reuse_score,
            "structural_pass": result.structural_result.passed,
            "overall_quality": self._calculate_overall_score(result)
        }
    
    def _calculate_overall_score(self, result) -> float:
        """Calculate overall quality score."""
        # Weighted average
        namespace_weight = 0.6
        structural_weight = 0.4
        
        namespace_score = result.namespace_result.reuse_score
        structural_score = 1.0 if result.structural_result.passed else 0.5
        
        return (namespace_score * namespace_weight + 
                structural_score * structural_weight)
    
    def _show_final_summary(self, code: str, scores: Dict):
        """Show final summary."""
        summary = {
            "namespace_reuse": scores.get("namespace_reuse", 0) * 100,
            "overall_quality": scores.get("overall_quality", 0) * 100,
            "status": "SUCCESS" if scores.get("namespace_reuse", 0) >= 0.4 else "NEEDS_WORK"
        }
        self.ui.show_summary(summary)
```

### Main Demo Script

```python
# demo.py

import argparse
import os
import sys
from pathlib import Path

from src.demo.demo_orchestrator import DemoOrchestrator
from src.utils.logger import Logger, get_logger

# Setup logging
Logger.setup(level="INFO", log_file="./logs/demo.log")
logger = get_logger(__name__)

def main():
    """Main demo entry point."""
    parser = argparse.ArgumentParser(
        description="Context-Aware Code Generation Demo"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository path or GitHub URL"
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Code generation request"
    )
    parser.add_argument(
        "--target-file",
        required=True,
        help="Target file for code generation"
    )
    parser.add_argument(
        "--mode",
        default="legacy",
        choices=["legacy", "greenfield"],
        help="Agent mode"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum refactor iterations"
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not set in environment")
        sys.exit(1)
    
    try:
        # Create orchestrator
        orchestrator = DemoOrchestrator(args.repo, api_key)
        
        # Run demo
        code, scores = orchestrator.run_demo(
            user_query=args.query,
            target_file=args.target_file,
            mode=args.mode,
            max_iterations=args.max_iterations
        )
        
        logger.info("Demo completed successfully")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Usage Examples

### Basic Demo
```bash
python demo.py \
  --repo ./sample_repo \
  --query "Add email validation to user registration" \
  --target-file src/services/user_service.py
```

### With GitHub URL
```bash
python demo.py \
  --repo https://github.com/user/project \
  --query "Create a new payment processing function" \
  --target-file src/services/payment.py \
  --mode greenfield
```

### Custom Iterations
```bash
python demo.py \
  --repo ./sample_repo \
  --query "Refactor authentication logic" \
  --target-file src/auth/authenticator.py \
  --max-iterations 5
```

## Recording the Demo Video

### Preparation
1. Clean terminal (clear history)
2. Set terminal size: 120x40 characters
3. Use a dark theme for better contrast
4. Test the full flow once

### Recording Tools
- **Windows**: OBS Studio, ShareX
- **Mac**: QuickTime, ScreenFlow
- **Linux**: SimpleScreenRecorder, OBS Studio

### Recording Tips
1. Start with welcome screen (2-3 seconds)
2. Show repository input
3. Let indexing run (speed up in editing if needed)
4. Show the query clearly
5. Let code generation stream
6. Highlight the score dashboard
7. Show refactor iteration if it happens
8. End with summary screen (3-4 seconds)

### Video Editing
- Add background music (subtle, non-distracting)
- Add text overlays explaining key concepts
- Speed up slow parts (indexing, waiting)
- Add zoom-ins on important scores
- Total length: 2-3 minutes ideal for hackathon

## Testing Checklist

Before recording:
- [ ] All dependencies installed (`pip install rich`)
- [ ] Sample repository ready
- [ ] GEMINI_API_KEY set in environment
- [ ] Test query prepared
- [ ] Terminal size and theme configured
- [ ] Demo runs without errors
- [ ] Scores display correctly
- [ ] Refactor loop works
- [ ] Summary shows properly

## Troubleshooting

### Issue: Rich not displaying colors
**Solution**: Ensure terminal supports ANSI colors, use `--force-terminal` flag

### Issue: Indexing takes too long
**Solution**: Use smaller sample repository for demo

### Issue: Agent not generating code
**Solution**: Check GEMINI_API_KEY, verify API quota

### Issue: Scores always 0%
**Solution**: Verify metric orchestrator integration, check repository has functions

## Next Steps

1. **Implement UI Components** - Start with `ui_components.py`
2. **Implement Orchestrator** - Create `demo_orchestrator.py`
3. **Create Main Script** - Build `demo.py`
4. **Test Thoroughly** - Run multiple times with different queries
5. **Record Video** - Capture the demo
6. **Create Slides** - Explain architecture and innovation

## Time Estimate

- UI Components: 1-1.5 hours
- Demo Orchestrator: 1-1.5 hours
- Main Script: 0.5 hours
- Testing & Refinement: 0.5-1 hour
- **Total: 3-4 hours**

## Success Criteria

✅ Beautiful terminal UI with colors and formatting
✅ Live progress bars during indexing
✅ Clear score visualization with thresholds
✅ Automatic refactor loop working
✅ Professional summary output
✅ Smooth demo flow for video recording
✅ Clearly demonstrates novel approach

---

**Ready to implement!** Follow this guide step-by-step to create an impressive demo for your hackathon video. 🚀