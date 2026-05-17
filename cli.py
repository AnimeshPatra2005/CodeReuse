"""
CLI Interface for Context-Aware Code Generation Agent.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.indexing.indexer import Indexer
from src.agent.agent import Agent
from src.models.data_models import GenerationRequest, AgentMode
from src.utils.logger import Logger, get_logger
from src.utils.config import load_config

# Initialize logger
Logger.setup(level="INFO", log_file="./logs/cli.log")
logger = get_logger(__name__)


def index_command(args):
    """Index a repository."""
    logger.info(f"Indexing repository: {args.path}")
    
    try:
        indexer = Indexer(
            repository_path=args.path,
            exclude_patterns=args.exclude or []
        )
        
        metadata = indexer.index_repository()
        
        print("\n" + "="*80)
        print("INDEXING COMPLETED")
        print("="*80)
        print(f"Repository: {metadata.repository_path}")
        print(f"Total Files: {metadata.total_files}")
        print(f"Total Functions: {metadata.total_functions}")
        print(f"Total Imports: {metadata.total_imports}")
        print(f"Indexed At: {metadata.indexed_at}")
        print("="*80 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error indexing repository: {e}")
        print(f"Error: {e}")
        return 1


def generate_command(args):
    """Generate code."""
    logger.info(f"Generating code: {args.request}")
    
    try:
        # Check if repository is indexed
        if not Path("./chroma_db").exists():
            print("Error: Repository not indexed. Run 'index' command first.")
            return 1
        
        # Load config
        config = load_config()
        
        # Initialize components
        from src.indexing.vector_db import VectorDBManager
        from src.indexing.dependency_graph import DependencyGraphBuilder
        
        vector_db = VectorDBManager(
            persist_directory=config.indexing.vector_db.persist_directory,
            collection_name=config.indexing.vector_db.collection_name
        )
        
        dependency_graph = DependencyGraphBuilder()
        
        # Load existing dependency graph
        graph_path = Path(config.indexing.vector_db.persist_directory) / "dependency_graph.json"
        if graph_path.exists():
            dependency_graph.load_from_file(str(graph_path))
        
        # Initialize agent
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY not set in environment")
            return 1
        
        agent = Agent(vector_db, dependency_graph, api_key)
        
        # Create request
        mode = AgentMode.LEGACY if args.mode == "legacy" else AgentMode.GREENFIELD
        request = GenerationRequest(
            user_request=args.request,
            target_file=args.target_file,
            mode=mode,
            additional_context=args.context
        )
        
        # Generate code
        print("\n" + "="*80)
        print("GENERATING CODE")
        print("="*80)
        print(f"Request: {args.request}")
        print(f"Target File: {args.target_file}")
        print(f"Mode: {mode.value}")
        print("="*80 + "\n")
        
        response = agent.generate_code(request)
        
        if response.success:
            print("\n" + "="*80)
            print("CODE GENERATION SUCCESSFUL")
            print("="*80)
            print(f"Execution Time: {response.execution_time:.2f}s")
            print(f"Subtasks: {len(response.subtasks)}")
            
            if response.metrics:
                print(f"\nMetrics:")
                if response.metrics.namespace_result:
                    print(f"  Reuse Score: {response.metrics.namespace_result.reuse_score:.2%}")
                if response.metrics.structural_result:
                    print(f"  Max Similarity: {response.metrics.structural_result.max_similarity:.2%}")
                print(f"  Validation: {'PASSED' if response.metrics.passed else 'FAILED'}")
            
            print(f"\nSimilar Functions Used: {len(response.similar_functions_used)}")
            
            print("\n" + "-"*80)
            print("GENERATED CODE:")
            print("-"*80)
            print(response.generated_code)
            print("-"*80 + "\n")
            
            # Save to file if requested
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(response.generated_code)
                print(f"Code saved to: {args.output}\n")
            
        else:
            print("\n" + "="*80)
            print("CODE GENERATION FAILED")
            print("="*80)
            print(f"Error: {response.error_message}")
            print("="*80 + "\n")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        print(f"Error: {e}")
        return 1


def search_command(args):
    """Search for functions."""
    logger.info(f"Searching for: {args.query}")
    
    try:
        # Load config
        config = load_config()
        
        # Initialize vector DB
        from src.indexing.vector_db import VectorDBManager
        
        vector_db = VectorDBManager(
            persist_directory=config.indexing.vector_db.persist_directory,
            collection_name=config.indexing.vector_db.collection_name
        )
        
        # Search
        results = vector_db.search_similar(
            query=args.query,
            top_k=args.top_k,
            min_similarity=0.6,
            dynamic_k=True
        )
        
        print("\n" + "="*80)
        print(f"SEARCH RESULTS FOR: {args.query}")
        print("="*80)
        print(f"Found {len(results)} similar functions\n")
        
        for i, result in enumerate(results, 1):
            func = result.function
            print(f"{i}. {func.name} (similarity: {result.similarity_score:.2%})")
            print(f"   File: {func.file_path}")
            print(f"   Signature: {func.signature}")
            if func.docstring:
                print(f"   Doc: {func.docstring[:100]}...")
            print()
        
        print("="*80 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error searching: {e}")
        print(f"Error: {e}")
        return 1


def stats_command(args):
    """Show indexing statistics."""
    try:
        # Load config
        config = load_config()
        
        # Check if indexed
        if not Path(config.indexing.vector_db.persist_directory).exists():
            print("Error: Repository not indexed. Run 'index' command first.")
            return 1
        
        # Initialize vector DB
        from src.indexing.vector_db import VectorDBManager
        
        vector_db = VectorDBManager(
            persist_directory=config.indexing.vector_db.persist_directory,
            collection_name=config.indexing.vector_db.collection_name
        )
        
        stats = vector_db.get_stats()
        
        print("\n" + "="*80)
        print("INDEXING STATISTICS")
        print("="*80)
        print(f"Total Functions: {stats['total_functions']}")
        print(f"Collection: {stats['collection_name']}")
        print(f"Model: {stats['model_name']}")
        print(f"Dimension: {stats['dimension']}")
        print("="*80 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        print(f"Error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Context-Aware Code Generation Agent CLI"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index a repository")
    index_parser.add_argument("path", help="Path to repository")
    index_parser.add_argument("--exclude", nargs="+", help="Patterns to exclude")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate code")
    generate_parser.add_argument("request", help="Code generation request")
    generate_parser.add_argument("--target-file", required=True, help="Target file path")
    generate_parser.add_argument("--mode", choices=["legacy", "greenfield"], default="legacy", help="Generation mode")
    generate_parser.add_argument("--context", help="Additional context")
    generate_parser.add_argument("--output", help="Output file path")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for functions")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == "index":
        return index_command(args)
    elif args.command == "generate":
        return generate_command(args)
    elif args.command == "search":
        return search_command(args)
    elif args.command == "stats":
        return stats_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
