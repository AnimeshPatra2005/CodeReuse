"""
FastAPI Backend - Main API server with WebSocket support.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path
import asyncio
import json
from datetime import datetime

from src.models.data_models import GenerationRequest, GenerationResponse, AgentMode
from src.indexing.indexer import Indexer
from src.indexing.vector_db import VectorDBManager
from src.indexing.dependency_graph import DependencyGraphBuilder
from src.agent.agent import Agent
from src.utils.logger import get_logger, Logger
from src.utils.config import load_config
from src.utils.websocket_logger import setup_websocket_logging

# Initialize logger
Logger.setup(level="INFO", log_file="./logs/api.log")
logger = get_logger(__name__)

# Load configuration
config = load_config()

# Initialize FastAPI app
app = FastAPI(
    title="Context-Aware Code Generation Agent",
    description="AI-powered code generation with enforced code reuse",
    version="1.0.0"
)

# Configure CORS — allow all origins so the static frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
indexer: Optional[Indexer] = None
vector_db: Optional[VectorDBManager] = None
dependency_graph: Optional[DependencyGraphBuilder] = None
agent: Optional[Agent] = None
active_connections: List[WebSocket] = []


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")


manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    logger.info("Starting Context-Aware Code Generation Agent API...")
    
    # Get API key from environment
    api_key = os.getenv("HUGGINGFACE_API_TOKEN")
    if not api_key:
        logger.warning("HUGGINGFACE_API_TOKEN not set in environment")
    
    # Wire WebSocket handler so ALL Python log messages reach the frontend
    setup_websocket_logging(manager)
    logger.info("WebSocket log broadcasting enabled")
    
    logger.info("API server started successfully")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Context-Aware Code Generation Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "indexer": indexer is not None,
            "vector_db": vector_db is not None,
            "agent": agent is not None
        }
    }


@app.post("/index/repository")
async def index_repository(
    repository_path: str,
    exclude_patterns: Optional[List[str]] = None
):
    """
    Index a repository.
    
    Args:
        repository_path: Path to repository
        exclude_patterns: Patterns to exclude
    """
    global indexer, vector_db, dependency_graph, agent
    
    import subprocess
    import shutil
    import os
    
    try:
        logger.info(f"Starting repository indexing: {repository_path}")
        
        # Broadcast indexing start
        await manager.broadcast({
            "type": "indexing_started",
            "repository_path": repository_path
        })
        
        is_remote = repository_path.startswith("http://") or repository_path.startswith("https://")
        if is_remote:
            repo_name = repository_path.rstrip("/").split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            local_repo_path = f"./uploaded_repos/{repo_name}"
            
            # Smart caching: reuse existing clone if valid, only re-clone if corrupted
            already_cloned = os.path.exists(local_repo_path) and os.path.exists(os.path.join(local_repo_path, '.git'))
            
            if already_cloned:
                logger.info(f"Using cached clone: {local_repo_path}")
                await manager.broadcast({
                    "type": "log",
                    "level": "info",
                    "message": f"Using cached clone of {repo_name} (already on disk)",
                    "category": "clone"
                })
            else:
                # Remove any partial/empty directory before cloning
                if os.path.exists(local_repo_path):
                    try:
                        shutil.rmtree(local_repo_path)
                    except Exception as rm_err:
                        logger.warning(f"Could not remove existing dir: {rm_err}")
                        # Rename it instead as fallback
                        os.rename(local_repo_path, local_repo_path + "_old")
                
                logger.info(f"Cloning {repository_path} into {local_repo_path}...")
                await manager.broadcast({
                    "type": "log",
                    "level": "info",
                    "message": f"Running: git clone --depth=1 {repository_path}",
                    "category": "clone"
                })
                result = subprocess.run(
                    ["git", "clone", "--depth=1", repository_path, local_repo_path],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode != 0:
                    error_detail = result.stderr.strip() or result.stdout.strip() or "Unknown git error"
                    raise RuntimeError(f"git clone failed: {error_detail}")
                logger.info(f"Clone successful: {local_repo_path}")
        else:
            local_repo_path = repository_path
            
        # Initialize indexer
        indexer = Indexer(
            repository_path=local_repo_path,
            exclude_patterns=exclude_patterns or config.repository.exclude_patterns
        )
        
        # Run the blocking CPU/IO work in a thread pool so we don't freeze the event loop
        # (model loading + AST parsing + embedding can take 30-60s)
        logger.info("Starting AST parsing, graph building, and vector embedding...")
        loop = asyncio.get_event_loop()
        metadata = await loop.run_in_executor(None, indexer.index_repository)
        
        # Get components
        vector_db = indexer.vector_db
        dependency_graph = indexer.graph_builder
        
        # Initialize agent
        api_key = os.getenv("HUGGINGFACE_API_TOKEN")
        agent = Agent(vector_db, dependency_graph, api_key)
        
        # Broadcast indexing complete
        await manager.broadcast({
            "type": "indexing_completed",
            "metadata": metadata.model_dump()
        })
        
        logger.info("Repository indexing completed")
        
        
        # Get all files for the dropdown (not just python files)
        all_files = []
        for root, dirs, files in os.walk(local_repo_path):
            dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', 'venv', '__pycache__')]
            for f in files:
                all_files.append(os.path.abspath(os.path.join(root, f)))
                
        return {
            "status": "success",
            "metadata": metadata.model_dump(),
            "files": all_files
        }
        
    except Exception as e:
        logger.error(f"Error indexing repository: {e}")
        await manager.broadcast({
            "type": "indexing_error",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=GenerationResponse)
async def generate_code(request: GenerationRequest):
    """
    Generate code based on user request.
    
    Args:
        request: Generation request
    """
    global agent
    
    if agent is None:
        raise HTTPException(
            status_code=400,
            detail="Agent not initialized. Please index a repository first."
        )
    
    try:
        logger.info(f"Generating code for: {request.user_request[:100]}...")
        
        # Broadcast generation start
        await manager.broadcast({
            "type": "generation_started",
            "request": request.user_request
        })
        
        # Generate code
        response = agent.generate_code(request)
        
        # Broadcast generation complete
        await manager.broadcast({
            "type": "generation_completed",
            "success": response.success,
            "subtasks": len(response.subtasks)
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        await manager.broadcast({
            "type": "generation_error",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/functions")
async def search_functions(query: str, top_k: int = 10):
    """
    Search for similar functions.
    
    Args:
        query: Search query
        top_k: Number of results
    """
    global vector_db
    
    if vector_db is None:
        raise HTTPException(
            status_code=400,
            detail="Vector DB not initialized. Please index a repository first."
        )
    
    try:
        results = vector_db.search_similar(
            query=query,
            top_k=top_k,
            min_similarity=0.6,
            dynamic_k=True
        )
        
        return {
            "query": query,
            "results": [
                {
                    "function": result.function.model_dump(),
                    "similarity_score": result.similarity_score,
                    "rank": result.rank
                }
                for result in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching functions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get indexing statistics."""
    global indexer
    
    if indexer is None:
        raise HTTPException(
            status_code=400,
            detail="Indexer not initialized. Please index a repository first."
        )
    
    try:
        stats = indexer.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph")
async def get_graph():
    """Return dependency graph (file-level import graph) for D3 visualization."""
    global dependency_graph

    if dependency_graph is None:
        raise HTTPException(
            status_code=400,
            detail="Dependency graph not built. Please index a repository first."
        )

    try:
        return {
            "import_graph":   dict(dependency_graph.import_graph),
            "file_functions": dict(dependency_graph.file_functions),
            "call_graph":     dict(dependency_graph.call_graph),
        }
    except Exception as e:
        logger.error(f"Error serving dependency graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_message({"type": "pong"}, websocket)
            
            elif message.get("type") == "subscribe":
                await manager.send_message({
                    "type": "subscribed",
                    "status": "connected"
                }, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.post("/upload/repository")
async def upload_repository(files: List[UploadFile] = File(...)):
    """
    Upload repository files.
    
    Args:
        files: List of files to upload
    """
    try:
        # Create temporary directory for uploaded files
        upload_dir = Path("./uploaded_repos") / datetime.now().strftime("%Y%m%d_%H%M%S")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save files
        for file in files:
            if file.filename:
                file_path = upload_dir / file.filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
        
        logger.info(f"Uploaded {len(files)} files to {upload_dir}")
        
        return {
            "status": "success",
            "upload_path": str(upload_dir),
            "files_count": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """Get current configuration."""
    return {
        "agent_mode": config.agent.mode,
        "llm_model": config.agent.llm.model,
        "metrics": {
            "namespace_min_reuse": config.metrics.namespace.min_reuse_score,
            "structural_max_similarity": config.metrics.structural.max_similarity,
            "max_retries": config.metrics.retry.max_retries
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=True,
        log_level="info"
    )

# Made with Bob
