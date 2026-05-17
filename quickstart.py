"""
Quick Start Script for Context-Aware Code Generation Agent.
Demonstrates the complete workflow.
"""

import os
import sys
from pathlib import Path

# Check if .env exists
if not Path(".env").exists():
    print("⚠️  .env file not found!")
    print("Please create .env file with your GEMINI_API_KEY")
    print("\nSteps:")
    print("1. Copy .env.example to .env")
    print("2. Add your Gemini API key")
    print("3. Get API key from: https://makersuite.google.com/app/apikey")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    print("⚠️  GEMINI_API_KEY not set in .env file!")
    sys.exit(1)

from src.indexing.indexer import Indexer
from src.agent.agent import Agent
from src.models.data_models import GenerationRequest, AgentMode
from src.utils.logger import Logger, get_logger

# Initialize logger
Logger.setup(level="INFO")
logger = get_logger(__name__)

def main():
    """Run quick start demo."""
    
    print("\n" + "="*80)
    print("CONTEXT-AWARE CODE GENERATION AGENT - QUICK START")
    print("="*80 + "\n")
    
    # Step 1: Index sample repository
    print("📚 Step 1: Indexing sample repository...")
    print("-" * 80)
    
    indexer = Indexer(
        repository_path="./sample_repo",
        exclude_patterns=["*/tests/*", "*/__pycache__/*"]
    )
    
    metadata = indexer.index_repository()
    
    print(f"✅ Indexed {metadata.total_files} files with {metadata.total_functions} functions\n")
    
    # Step 2: Initialize agent
    print("🤖 Step 2: Initializing agent...")
    print("-" * 80)
    
    vector_db = indexer.vector_db
    dependency_graph = indexer.graph_builder
    api_key = os.getenv("GEMINI_API_KEY")
    
    agent = Agent(vector_db, dependency_graph, api_key)
    print("✅ Agent initialized\n")
    
    # Step 3: Generate code
    print("💻 Step 3: Generating code...")
    print("-" * 80)
    
    request = GenerationRequest(
        user_request="Add a function to validate phone numbers in international format",
        target_file="sample_repo/utils.py",
        mode=AgentMode.LEGACY
    )
    
    print(f"Request: {request.user_request}")
    print(f"Target: {request.target_file}")
    print(f"Mode: {request.mode.value}\n")
    
    response = agent.generate_code(request)
    
    # Step 4: Display results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80 + "\n")
    
    if response.success:
        print("✅ Code generation successful!\n")
        
        print(f"⏱️  Execution time: {response.execution_time:.2f}s")
        print(f"📋 Subtasks completed: {len(response.subtasks)}")
        
        if response.metrics:
            print(f"\n📊 Metrics:")
            if response.metrics.namespace_result:
                score = response.metrics.namespace_result.reuse_score
                print(f"   • Code reuse score: {score:.1%}")
                print(f"   • Functions reused: {len(response.metrics.namespace_result.repo_functions_used)}")
            
            if response.metrics.structural_result:
                sim = response.metrics.structural_result.max_similarity
                print(f"   • Max structural similarity: {sim:.1%}")
            
            status = "✅ PASSED" if response.metrics.passed else "❌ FAILED"
            print(f"   • Validation: {status}")
        
        print(f"\n🔍 Similar functions found: {len(response.similar_functions_used)}")
        
        if response.similar_functions_used:
            print("\nFunctions that could be reused:")
            for func in response.similar_functions_used[:3]:
                print(f"   • {func.name} - {func.file_path}")
        
        print("\n" + "-"*80)
        print("GENERATED CODE:")
        print("-"*80)
        print(response.generated_code)
        print("-"*80)
        
        # Save to file
        output_file = "generated_phone_validation.py"
        with open(output_file, 'w') as f:
            f.write(response.generated_code)
        print(f"\n💾 Code saved to: {output_file}")
        
    else:
        print("❌ Code generation failed!")
        print(f"Error: {response.error_message}")
    
    print("\n" + "="*80)
    print("QUICK START COMPLETED")
    print("="*80)
    
    print("\n📚 Next steps:")
    print("   1. Try the CLI: python cli.py --help")
    print("   2. Start API server: python -m src.api.main")
    print("   3. Index your own repository: python cli.py index /path/to/repo")
    print("   4. Read the README.md for more examples\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
