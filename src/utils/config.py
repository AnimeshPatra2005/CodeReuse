"""
Configuration loader and manager.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EmbedderConfig(BaseModel):
    """Embedder configuration."""
    model: str = "jinaai/jina-embeddings-v2-base-code"
    dimension: int = 768
    batch_size: int = 32


class VectorDBConfig(BaseModel):
    """Vector database configuration."""
    type: str = "chromadb"
    persist_directory: str = "./chroma_db"
    collection_name: str = "code_functions"


class IndexingConfig(BaseModel):
    """Indexing configuration."""
    embedder: EmbedderConfig = Field(default_factory=EmbedderConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: str = "gemini"
    model: str = "gemini-1.5-flash"
    temperature: float = 0.2
    max_tokens: int = 4096


class SubtaskConfig(BaseModel):
    """Subtask configuration."""
    max_subtasks: int = 5
    min_subtasks: int = 2


class AgentConfig(BaseModel):
    """Agent configuration."""
    mode: str = "legacy"
    llm: LLMConfig = Field(default_factory=LLMConfig)
    subtask: SubtaskConfig = Field(default_factory=SubtaskConfig)


class NamespaceMetricsConfig(BaseModel):
    """Namespace metrics configuration."""
    min_reuse_score: float = 0.4
    enabled: bool = True


class StructuralMetricsConfig(BaseModel):
    """Structural metrics configuration."""
    max_similarity: float = 0.85
    semantic_threshold: float = 0.75
    enabled: bool = True


class DependencyMetricsConfig(BaseModel):
    """Dependency metrics configuration."""
    check_breaking_changes: bool = True
    enabled: bool = True


class RetryConfig(BaseModel):
    """Retry configuration."""
    max_retries: int = 3
    enabled: bool = True


class MetricsConfig(BaseModel):
    """Metrics configuration."""
    namespace: NamespaceMetricsConfig = Field(default_factory=NamespaceMetricsConfig)
    structural: StructuralMetricsConfig = Field(default_factory=StructuralMetricsConfig)
    dependency: DependencyMetricsConfig = Field(default_factory=DependencyMetricsConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)


class GlobalContextConfig(BaseModel):
    """Global context configuration."""
    include_target_file: bool = True


class LocalContextConfig(BaseModel):
    """Local context configuration."""
    min_similarity: float = 0.7
    max_k: int = 5
    dynamic_k: bool = True


class ContextConfig(BaseModel):
    """Context configuration."""
    global_: GlobalContextConfig = Field(default_factory=GlobalContextConfig, alias="global")
    local: LocalContextConfig = Field(default_factory=LocalContextConfig)
    
    class Config:
        populate_by_name = True


class RepositoryConfig(BaseModel):
    """Repository configuration."""
    path: str = "./sample_repo"
    exclude_patterns: list[str] = Field(default_factory=lambda: [
        "*/tests/*", "*/venv/*", "*/__pycache__/*", "*.pyc", ".git/*"
    ])


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    file: str = "./logs/agent.log"
    rotation: str = "10 MB"


class APIConfig(BaseModel):
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:3000", "http://localhost:5173"
    ])
    websocket_enabled: bool = True


class Config(BaseModel):
    """Main configuration."""
    repository: RepositoryConfig = Field(default_factory=RepositoryConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    api: APIConfig = Field(default_factory=APIConfig)


class ConfigLoader:
    """Configuration loader and manager."""
    
    _instance: Optional['ConfigLoader'] = None
    _config: Optional[Config] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(self, config_path: str = "config.yaml") -> Config:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Config object
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            print(f"Warning: Config file {config_path} not found. Using defaults.")
            self._config = Config()
            return self._config
        
        with open(config_file, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        self._config = Config(**config_dict)
        return self._config
    
    def get(self) -> Config:
        """
        Get current configuration.
        
        Returns:
            Config object
        """
        if self._config is None:
            return self.load()
        return self._config
    
    def reload(self, config_path: str = "config.yaml") -> Config:
        """
        Reload configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Config object
        """
        return self.load(config_path)


# Singleton instance
config_loader = ConfigLoader()


def get_config() -> Config:
    """Get the current configuration."""
    return config_loader.get()


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from file."""
    return config_loader.load(config_path)

# Made with Bob
