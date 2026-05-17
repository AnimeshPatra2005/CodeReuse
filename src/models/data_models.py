"""
Data models for the Context-Aware Code Generation Agent.
Defines all core data structures used throughout the system.
"""

from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel, Field
from enum import Enum


class AgentMode(str, Enum):
    """Operating mode for the agent."""
    LEGACY = "legacy"
    GREENFIELD = "greenfield"


class ImportNode(BaseModel):
    """Represents an import statement in Python code."""
    module: str
    names: List[str] = Field(default_factory=list)
    alias: Optional[str] = None
    line_number: int
    is_from_import: bool = False
    
    class Config:
        frozen = True


class FunctionNode(BaseModel):
    """Represents a function definition with metadata."""
    name: str
    file_path: str
    signature: str
    parameters: List[str] = Field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    body_preview: str = ""  # First 3 statements, textified
    line_start: int
    line_end: int
    calls: List[str] = Field(default_factory=list)  # Functions called within this function
    imports_used: List[str] = Field(default_factory=list)
    
    def get_textified(self) -> str:
        """Get compact textified representation for embedding."""
        return f"{self.signature} | {self.body_preview}"
    
    class Config:
        frozen = True


class Subtask(BaseModel):
    """Represents a decomposed subtask."""
    id: int
    description: str
    estimated_complexity: str = "medium"  # low, medium, high
    dependencies: List[int] = Field(default_factory=list)  # IDs of dependent subtasks
    
    class Config:
        frozen = True


class ContextWindow(BaseModel):
    """Context provided to LLM for code generation."""
    global_context: str = ""  # Target file content
    local_context: List[FunctionNode] = Field(default_factory=list)  # Similar functions
    subtask_memory: List[str] = Field(default_factory=list)  # Previously created function signatures
    current_subtask: Optional[Subtask] = None
    
    def get_context_string(self) -> str:
        """Format context for LLM prompt."""
        context_parts = []
        
        if self.global_context:
            context_parts.append(f"=== TARGET FILE ===\n{self.global_context}\n")
        
        if self.local_context:
            context_parts.append("=== SIMILAR EXISTING FUNCTIONS (REUSE THESE) ===")
            for func in self.local_context:
                context_parts.append(
                    f"\nFunction: {func.name}\n"
                    f"File: {func.file_path}\n"
                    f"Signature: {func.signature}\n"
                    f"Docstring: {func.docstring or 'N/A'}\n"
                )
        
        if self.subtask_memory:
            context_parts.append("\n=== FUNCTIONS CREATED IN PREVIOUS SUBTASKS ===")
            context_parts.extend(self.subtask_memory)
        
        return "\n".join(context_parts)


class NamespaceResult(BaseModel):
    """Result of namespace invocation checking."""
    called_functions: Set[str] = Field(default_factory=set)
    repo_functions_used: Set[str] = Field(default_factory=set)
    reuse_score: float = 0.0
    passed: bool = False
    details: str = ""
    
    class Config:
        arbitrary_types_allowed = True


class StructuralViolation(BaseModel):
    """Represents a structural similarity violation."""
    generated_function: str
    similar_repo_function: str
    similarity_score: float
    repo_file_path: str
    explanation: str


class StructuralResult(BaseModel):
    """Result of structural similarity checking."""
    violations: List[StructuralViolation] = Field(default_factory=list)
    max_similarity: float = 0.0
    passed: bool = True
    details: str = ""


class BreakingChange(BaseModel):
    """Represents a breaking change in dependencies."""
    affected_file: str
    affected_function: str
    issue: str
    suggestion: str


class DependencyResult(BaseModel):
    """Result of dependency validation."""
    breaking_changes: List[BreakingChange] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    passed: bool = True
    details: str = ""


class MetricResult(BaseModel):
    """Combined result of all metric validations."""
    passed: bool
    namespace_result: Optional[NamespaceResult] = None
    structural_result: Optional[StructuralResult] = None
    dependency_result: Optional[DependencyResult] = None
    llm_validation: Optional[Dict[str, Any]] = None  # LLM-based dependent file validation
    explanation: str = ""
    retry_count: int = 0
    
    def get_failure_summary(self) -> str:
        """Get human-readable summary of failures."""
        failures = []
        
        if self.namespace_result and not self.namespace_result.passed:
            failures.append(f"Namespace Check: {self.namespace_result.details}")
        
        if self.structural_result and not self.structural_result.passed:
            failures.append(f"Structural Check: {self.structural_result.details}")
        
        if self.dependency_result and not self.dependency_result.passed:
            failures.append(f"Dependency Check: {self.dependency_result.details}")
        
        return "\n".join(failures) if failures else "All checks passed"


class GenerationRequest(BaseModel):
    """Request for code generation."""
    user_request: str
    target_file: str
    mode: AgentMode = AgentMode.LEGACY
    additional_context: Optional[str] = None


class GenerationResponse(BaseModel):
    """Response from code generation."""
    generated_code: str
    subtasks: List[Subtask]
    metrics: Optional[MetricResult] = None
    similar_functions_used: List[FunctionNode] = Field(default_factory=list)
    execution_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


class IndexMetadata(BaseModel):
    """Metadata about the indexed repository."""
    repository_path: str
    total_files: int
    total_functions: int
    total_imports: int
    indexed_at: str
    index_version: str = "1.0.0"
    excluded_patterns: List[str] = Field(default_factory=list)


class DependencyGraph(BaseModel):
    """Represents the dependency graph structure."""
    import_graph: Dict[str, List[str]] = Field(default_factory=dict)  # file -> imported files
    call_graph: Dict[str, List[str]] = Field(default_factory=dict)  # function -> called functions
    function_registry: Dict[str, str] = Field(default_factory=dict)  # function name -> file path
    
    class Config:
        arbitrary_types_allowed = True


class SearchResult(BaseModel):
    """Result from vector similarity search."""
    function: FunctionNode
    similarity_score: float
    rank: int


class ValidationConfig(BaseModel):
    """Configuration for validation thresholds."""
    min_reuse_score: float = 0.4
    max_structural_similarity: float = 0.85
    semantic_threshold: float = 0.75
    max_retries: int = 3


class EmbeddingMetadata(BaseModel):
    """Metadata stored with embeddings in vector DB."""
    function_name: str
    file_path: str
    signature: str
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    full_code: str
    line_start: int
    line_end: int
    textified: str


class TaskDecomposition(BaseModel):
    """Result of task decomposition."""
    subtasks: List[Subtask]
    reasoning: str
    estimated_total_time: str


class CodeAnalysis(BaseModel):
    """Analysis of generated code."""
    functions_defined: List[str]
    functions_called: List[str]
    imports_added: List[str]
    complexity_score: float
    lines_of_code: int

# Made with Bob
