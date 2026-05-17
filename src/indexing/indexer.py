"""
Indexer Orchestrator - Coordinates parsing, dependency graph building, and vector embedding.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from src.indexing.ast_parser import ASTParser
from src.indexing.dependency_graph import DependencyGraphBuilder
from src.indexing.vector_db import VectorDBManager
from src.models.data_models import FunctionNode, ImportNode, IndexMetadata
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)


class Indexer:
    """Main indexer that orchestrates repository analysis and indexing."""
    
    def __init__(
        self,
        repository_path: str,
        exclude_patterns: Optional[List[str]] = None,
        config_override: Optional[Dict] = None
    ):
        """
        Initialize Indexer.
        
        Args:
            repository_path: Path to repository to index
            exclude_patterns: Patterns to exclude from indexing
            config_override: Optional config overrides
        """
        self.repository_path = Path(repository_path)
        self.exclude_patterns = exclude_patterns or []
        
        # Load config
        config = get_config()
        if config_override:
            # Apply overrides (simplified)
            pass
        
        # Initialize components
        self.parser = ASTParser()
        self.graph_builder = DependencyGraphBuilder()
        
        # Initialize vector DB
        vector_config = config.indexing.vector_db
        embedder_config = config.indexing.embedder
        
        self.vector_db = VectorDBManager(
            persist_directory=vector_config.persist_directory,
            collection_name=vector_config.collection_name,
            model_name=embedder_config.model,
            dimension=embedder_config.dimension
        )
        
        # Storage for parsed data
        self.functions_by_file: Dict[str, List[FunctionNode]] = {}
        self.imports_by_file: Dict[str, List[ImportNode]] = {}
        self.all_functions: List[FunctionNode] = []
    
    def index_repository(self) -> IndexMetadata:
        """
        Index entire repository.
        
        Returns:
            IndexMetadata with indexing statistics
        """
        logger.info(f"Starting repository indexing: {self.repository_path}")
        start_time = datetime.now()
        
        # Find all Python files
        python_files = self._find_python_files()
        logger.info(f"Found {len(python_files)} Python files")
        
        if not python_files:
            logger.warning("No Python files found to index")
            return self._create_metadata(0, 0, 0)
        
        # Parse all files
        self._parse_files(python_files)
        
        # Build dependency graph
        logger.info("Building dependency graph...")
        dependency_graph = self.graph_builder.build_graph(
            self.functions_by_file,
            self.imports_by_file
        )
        
        # Save dependency graph
        graph_path = Path(self.vector_db.persist_directory) / "dependency_graph.json"
        self.graph_builder.save_to_file(str(graph_path))
        
        # Add functions to vector database
        logger.info("Adding functions to vector database...")
        self.vector_db.add_functions(self.all_functions)
        
        # Create and save metadata
        metadata = self._create_metadata(
            len(python_files),
            len(self.all_functions),
            sum(len(imports) for imports in self.imports_by_file.values())
        )
        
        metadata_path = Path(self.vector_db.persist_directory) / "index_metadata.json"
        self._save_metadata(metadata, str(metadata_path))
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Indexing completed in {elapsed:.2f} seconds")
        
        return metadata
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in repository."""
        python_files = []
        
        for file_path in self.repository_path.rglob("*.py"):
            # Check if file should be excluded
            if self._should_exclude(file_path):
                continue
            
            python_files.append(file_path)
        
        return python_files
    
    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded based on patterns."""
        file_str = str(file_path)
        
        for pattern in self.exclude_patterns:
            # Simple pattern matching (can be enhanced with fnmatch)
            pattern_clean = pattern.replace('*/', '').replace('/*', '')
            if pattern_clean in file_str:
                return True
        
        return False
    
    def _parse_files(self, python_files: List[Path]):
        """Parse all Python files."""
        total = len(python_files)
        
        for i, file_path in enumerate(python_files, 1):
            if i % 10 == 0:
                logger.info(f"Parsing progress: {i}/{total}")
            
            try:
                functions, imports = self.parser.parse_file(str(file_path))
                
                if functions:
                    self.functions_by_file[str(file_path)] = functions
                    self.all_functions.extend(functions)
                
                if imports:
                    self.imports_by_file[str(file_path)] = imports
                    
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")
    
    def _create_metadata(
        self,
        total_files: int,
        total_functions: int,
        total_imports: int
    ) -> IndexMetadata:
        """Create index metadata."""
        return IndexMetadata(
            repository_path=str(self.repository_path),
            total_files=total_files,
            total_functions=total_functions,
            total_imports=total_imports,
            indexed_at=datetime.now().isoformat(),
            excluded_patterns=self.exclude_patterns
        )
    
    def _save_metadata(self, metadata: IndexMetadata, path: str):
        """Save metadata to file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(metadata.model_dump(), f, indent=2)
        
        logger.info(f"Metadata saved to {path}")
    
    def update_file(self, file_path: str) -> bool:
        """
        Update index for a single file (incremental update).
        
        Args:
            file_path: Path to file to update
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Updating index for: {file_path}")
        
        try:
            # Parse file
            functions, imports = self.parser.parse_file(file_path)
            
            # Delete old functions from vector DB
            self.vector_db.delete_file_functions(file_path)
            
            # Add new functions
            if functions:
                self.vector_db.add_functions(functions)
                self.functions_by_file[file_path] = functions
            else:
                self.functions_by_file.pop(file_path, None)
            
            # Update imports
            if imports:
                self.imports_by_file[file_path] = imports
            else:
                self.imports_by_file.pop(file_path, None)
            
            # Rebuild dependency graph
            dependency_graph = self.graph_builder.build_graph(
                self.functions_by_file,
                self.imports_by_file
            )
            
            # Save updated graph
            graph_path = Path(self.vector_db.persist_directory) / "dependency_graph.json"
            self.graph_builder.save_to_file(str(graph_path))
            
            logger.info(f"Successfully updated index for {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating index for {file_path}: {e}")
            return False
    
    def update_files(self, file_paths: List[str]) -> Dict[str, bool]:
        """
        Update index for multiple files.
        
        Args:
            file_paths: List of file paths to update
            
        Returns:
            Dict mapping file paths to success status
        """
        results = {}
        
        for file_path in file_paths:
            results[file_path] = self.update_file(file_path)
        
        return results
    
    def delete_file(self, file_path: str):
        """
        Remove a file from the index.
        
        Args:
            file_path: Path to file to remove
        """
        logger.info(f"Removing file from index: {file_path}")
        
        # Remove from vector DB
        self.vector_db.delete_file_functions(file_path)
        
        # Remove from internal storage
        self.functions_by_file.pop(file_path, None)
        self.imports_by_file.pop(file_path, None)
        
        # Rebuild dependency graph
        dependency_graph = self.graph_builder.build_graph(
            self.functions_by_file,
            self.imports_by_file
        )
        
        # Save updated graph
        graph_path = Path(self.vector_db.persist_directory) / "dependency_graph.json"
        self.graph_builder.save_to_file(str(graph_path))
        
        logger.info(f"File removed from index: {file_path}")
    
    def get_stats(self) -> Dict:
        """
        Get indexing statistics.
        
        Returns:
            Dict with statistics
        """
        return {
            'repository_path': str(self.repository_path),
            'total_files': len(self.functions_by_file),
            'total_functions': len(self.all_functions),
            'total_imports': sum(len(imports) for imports in self.imports_by_file.values()),
            'vector_db_stats': self.vector_db.get_stats()
        }
    
    def load_existing_index(self) -> bool:
        """
        Load existing index from disk.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load dependency graph
            graph_path = Path(self.vector_db.persist_directory) / "dependency_graph.json"
            if graph_path.exists():
                self.graph_builder.load_from_file(str(graph_path))
                logger.info("Loaded existing dependency graph")
            
            # Load metadata
            metadata_path = Path(self.vector_db.persist_directory) / "index_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"Loaded index metadata: {metadata['total_functions']} functions")
            
            # Vector DB is automatically loaded by ChromaDB
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading existing index: {e}")
            return False

# Made with Bob
