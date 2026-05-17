"""
Main demo script for Context-Aware Code Generation Agent.
Supports both GitHub URLs and local repository paths.
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.demo.demo_orchestrator import DemoOrchestrator
from src.utils.logger import Logger, get_logger
from src.utils.quiet_logger import setup_quiet_mode

# Load environment variables from .env file
load_dotenv()

# Setup quiet mode to suppress verbose warnings
setup_quiet_mode()

# Setup logging - reduce verbosity for cleaner demo output
Logger.setup(level="WARNING", log_file="./logs/demo.log")
logger = get_logger(__name__)


def main():
    """Main demo entry point."""
    parser = argparse.ArgumentParser(
        description="Context-Aware Code Generation Demo - Paste GitHub URL and watch the magic!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using GitHub URL (automatically clones)
  python demo.py --repo https://github.com/user/project --query "Add validation" --target-file src/app.py
  
  # Using local repository
  python demo.py --repo ./sample_repo --query "Add email validation" --target-file user_service.py
  
  # With custom iterations
  python demo.py --repo https://github.com/user/project --query "Refactor auth" --target-file auth.py --max-iterations 5
        """
    )
    
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub URL (will be auto-cloned) or local repository path"
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Code generation request (what you want to build)"
    )
    parser.add_argument(
        "--target-file",
        required=True,
        help="Target file for code generation (relative to repo root)"
    )
    parser.add_argument(
        "--mode",
        default="legacy",
        choices=["legacy", "greenfield"],
        help="Agent mode: 'legacy' for existing codebases, 'greenfield' for new projects"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum refactor iterations (default: 3)"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't delete cloned repository after demo (for debugging)"
    )
    
    args = parser.parse_args()
    
    # Get API key (Hugging Face for IBM Granite)
    api_key = os.getenv("HUGGINGFACE_API_TOKEN")
    if not api_key:
        print("\n" + "="*80)
        print("❌ ERROR: HUGGINGFACE_API_TOKEN not set in environment")
        print("="*80)
        print("\nPlease set your Hugging Face API token:")
        print("  Windows (PowerShell): $env:HUGGINGFACE_API_TOKEN='your-token'")
        print("  Linux/Mac: export HUGGINGFACE_API_TOKEN='your-token'")
        print("\nOr add it to a .env file in the project root.")
        print("Get your token from: https://huggingface.co/settings/tokens")
        print("="*80 + "\n")
        sys.exit(1)
    
    try:
        # Create orchestrator
        orchestrator = DemoOrchestrator(args.repo, api_key)
        
        # Run demo
        print("\n" + "="*80)
        print("🚀 Starting Context-Aware Code Generation Demo")
        print("="*80 + "\n")
        
        code, scores = orchestrator.run_demo(
            user_query=args.query,
            target_file=args.target_file,
            mode=args.mode,
            max_iterations=args.max_iterations
        )
        
        logger.info("Demo completed successfully")
        
        # Show output location
        print("\n" + "="*80)
        print("📝 Generated Code:")
        print("="*80)
        print(code)
        print("="*80 + "\n")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("👋 Demo interrupted by user")
        print("="*80 + "\n")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print("\n" + "="*80)
        print(f"❌ Demo failed: {e}")
        print("="*80)
        print("\nFor detailed error information, check: ./logs/demo.log")
        print("="*80 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
