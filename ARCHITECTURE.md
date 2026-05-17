# Context-Aware Code Generation Agent - Architecture Guide

## Executive Summary

A system that enforces deterministic code reuse in AI-generated code through AST analysis, vector similarity search, and structural verification. Prevents code duplication by ensuring AI agents leverage existing utilities instead of creating redundant implementations.

**Core Innovation**: Dual-phase verification (namespace checking + structural similarity) with rolling subtask context management.

---

## System Architecture

### Three-Phase Pipeline

1. **Phase 1: Offline Indexing Engine** - Parse repository, build dependency graphs, create vector embeddings
2. **Phase 2: Task Planner & Agent** - Decompose tasks, manage context, generate code with LLM
3. **Phase 3: Metric Validation** - Verify code reuse, detect plagiarism, validate dependencies

### System Flow

```
Repository → Indexing → Vector DB + Dependency Graph
                              ↓
User Request → Task Decomposition → Subtasks (s1, s2, s3...)
                              ↓
For each subtask:
  Global Context (target file) + Local Context (top-k similar functions)
                              ↓
  LLM Code Generation
                              ↓
  Metric Validation (Legacy Mode only)
                              ↓
  Update Subtask Memory → Next Subtask
                              ↓
Final Code → Dependency Validation → Output
```

---

## Phase 1: Offline Indexing Engine

### Purpose
One-time repository analysis to extract all functions, dependencies, and create searchable embeddings.

### Components

#### 1. AST Parser (`ast_parser.py`)
- Parse Python files using `ast.parse()`
- Extract: imports, function definitions, function calls
- **Textification**: Convert functions to indexable format (signature + first 3 statements, normalized)

#### 2. Dependency Graph Builder (`dependency_graph.py`)
- **Import Graph**: File-level dependencies (which file imports what)
- **Call Graph**: Function-level dependencies (which function calls what)
- Provides: `get_dependents()`, `get_transitive_dependencies()`, `get_function_dependencies()`

#### 3. Vector Database Manager (`vector_db.py`)
- **Technology**: ChromaDB with Jina Code Embeddings V2 (768-dim)
- **Storage**: Textified functions + metadata (file path, signature, parameters, full code)
- **Search**: Dynamic k-retrieval with similarity threshold (min_similarity=0.7, max_k=5)

#### 4. Indexer Orchestrator (`indexer.py`)
- Coordinates: parsing → dependency graph building → embedding → storage
- Outputs: `chroma_db/`, `dependency_graph.json`, `index_metadata.json`
- Supports incremental updates for modified files

---

## Phase 2: Task Planner & Agent Orchestration

### Purpose
Break down user requests into manageable subtasks and generate code with efficient context management.

### Components

#### 1. Subtask Decomposer (`subtask_decomposer.py`)
- Uses LLM to break user request into 3-5 isolated subtasks
- Each subtask: independently executable, clear input/output, single responsibility

#### 2. Context Builder (`context_builder.py`)
- **Global Context**: Target file content (persists across all subtasks)
- **Local Context**: Top-k semantically similar functions from vector DB (ephemeral per subtask)
- **Cumulative Subtask Memory**: Function signatures created in previous subtasks (prevents duplication within session)
- **Dynamic k-Retrieval**: Only retrieve functions above similarity threshold, cap at max_k

#### 3. Agent Orchestrator (`agent.py`)
- Main workflow coordinator
- For each subtask:
  1. Build global + local context
  2. Generate code with LLM
  3. Validate (if Legacy Mode)
  4. Update subtask memory
  5. Clear local context
- Combines all subtask outputs into final code

---

## Phase 3: Metric Validation System

### Purpose
Enforce code reuse through deterministic verification (Legacy Mode only).

### Components

#### 1. Namespace Invocation Checker (`namespace_checker.py`)
- Parse generated code with AST
- Extract all function calls (`ast.Call` nodes)
- Resolve to fully qualified names (handle imports, aliases)
- Calculate reuse score: `|called_functions ∩ repo_functions| / |called_functions|`
- **Threshold**: Minimum 40% reuse score to pass

#### 2. Structural Similarity Matcher (`structural_matcher.py`)
- Detects code plagiarism (copying logic instead of calling functions)
- Extract structural tokens from AST (control flow, operations, assignments - no variable names)
- Calculate Jaccard similarity with sliding window
- **Violation**: Structural similarity ≥85% + namespace reuse = 0% + semantic similarity ≥75%
- Prevents agent from copying function internals instead of calling the function

#### 3. Dependency Validator (`dependency_validator.py`)
- Check if new code breaks existing call sites
- For each dependent file:
  - Parse and find calls to modified functions
  - Verify signature compatibility
  - Check import resolution
- Report breaking changes

#### 4. Explanation Generator (`explanation_generator.py`)
- Generate human-readable explanations when validation fails
- Include: what failed, why, how to fix, code examples
- Suggest specific functions to reuse

#### 5. Metric Orchestrator (`metric.py`)
- Runs all validators in sequence
- Implements retry logic (max 3 retries)
- On failure: generate explanation → pass to LLM → regenerate code → validate again

---

## Mode System

### Legacy Mode (Default)
- **Use Case**: Modifying existing codebases with established utilities
- **Behavior**: Full metric validation, enforces code reuse, retrieves similar functions
- **Thresholds**: 40% min reuse, 85% max structural similarity, 75% semantic similarity

### Greenfield Mode
- **Use Case**: New projects or completely new features
- **Behavior**: No metric validation, basic syntax/import checks only
- **Assumption**: Modern AI IDE handles basic validation

---

## Key Algorithms

### 1. Textification
Convert function to compact, searchable representation:
- Signature (name + params + return type)
- First 3 executable statements
- Normalize variable names to placeholders
- Result: `"func_name(params) -> return | stmt1 | stmt2 | stmt3"`

### 2. Call Graph Construction
- Build function registry (name → file path mapping)
- For each function, resolve its calls:
  - Imported functions → resolve to actual file
  - Local functions → resolve within same file
  - Track transitive dependencies

### 3. Dynamic k-Retrieval
- Query vector DB with high k (e.g., 10)
- Filter by min_similarity threshold
- Cap at max_k to prevent context bloat
- Returns variable number of results based on relevance

### 4. Structural Plagiarism Detection
- Extract AST node types (If, For, Assign, Return, etc.)
- Remove all identifiers (variables, functions, strings, numbers)
- Calculate Jaccard similarity with sliding window
- Flag if: high structural similarity + no function reuse + same semantic purpose

### 5. Reuse Score Calculation
```
reuse_score = |called_functions ∩ repo_functions| / |called_functions|
```
- 0.0 = no reuse (all new code)
- 1.0 = perfect reuse (all calls to existing functions)
- Handle edge case: 0 function calls = 1.0 (simple logic, no penalty)

---

## Data Models

### Core Data Structures
- `FunctionNode`: name, file_path, signature, parameters, return_type, docstring, body_preview, line_start, line_end, calls
- `ImportNode`: module, names, alias, line_number
- `Subtask`: id, description, estimated_complexity
- `NamespaceResult`: called_functions, repo_functions_used, reuse_score, passed
- `StructuralResult`: violations, max_similarity, passed
- `ValidationResult`: passed, breaking_changes, warnings
- `MetricResult`: passed, namespace_result, structural_result, dependency_result, explanation, retry_count

---

## Configuration

### Key Settings (`config.yaml`)
```yaml
repository:
  path: "/path/to/repo"
  exclude_patterns: ["*/tests/*", "*/venv/*"]

indexing:
  embedder:
    model: "jinaai/jina-embeddings-v2-base-code"
    dimension: 768
  vector_db:
    type: "chromadb"
    persist_directory: "./chroma_db"

agent:
  mode: "legacy"  # or "greenfield"
  llm:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.2

metrics:
  namespace:
    min_reuse_score: 0.4
  structural:
    max_similarity: 0.85
    semantic_threshold: 0.75
  retry:
    max_retries: 3

context:
  local:
    min_similarity: 0.7
    max_k: 5
```

---

## Implementation Order

### Week 1: Foundation
1. Project structure setup
2. Data models (`models/data_models.py`)
3. AST parser (`indexing/ast_parser.py`)
4. Dependency graph (`indexing/dependency_graph.py`)

### Week 2: Indexing
5. Vector DB manager (`indexing/vector_db.py`)
6. Indexer orchestrator (`indexing/indexer.py`)
7. Test on sample repository

### Week 3: Agent System
8. Subtask decomposer (`agent/subtask_decomposer.py`)
9. Context builder (`agent/context_builder.py`)
10. Agent orchestrator (`agent/agent.py`)

### Week 4: Metric System
11. Namespace checker (`metrics/namespace_checker.py`)
12. Structural matcher (`metrics/structural_matcher.py`)
13. Dependency validator (`metrics/dependency_validator.py`)
14. Explanation generator (`metrics/explanation_generator.py`)
15. Metric orchestrator (`metrics/metric.py`)

### Week 5: Integration
16. End-to-end integration
17. CLI interface
18. Comprehensive testing
19. Documentation

---

## Project Structure

```
context-aware-agent/
├── src/
│   ├── indexing/
│   │   ├── ast_parser.py
│   │   ├── dependency_graph.py
│   │   ├── vector_db.py
│   │   └── indexer.py
│   ├── agent/
│   │   ├── subtask_decomposer.py
│   │   ├── context_builder.py
│   │   └── agent.py
│   ├── metrics/
│   │   ├── namespace_checker.py
│   │   ├── structural_matcher.py
│   │   ├── dependency_validator.py
│   │   ├── explanation_generator.py
│   │   └── metric.py
│   ├── models/
│   │   └── data_models.py
│   └── utils/
│       ├── config.py
│       └── logger.py
├── tests/
├── config.yaml
├── requirements.txt
└── README.md
```

---

## Testing Strategy

### Unit Tests (80% coverage minimum)
- AST parser: imports, functions, calls extraction
- Dependency graph: import/call graph construction, traversal
- Vector DB: embedding, search, updates
- Namespace checker: function call detection, reuse score
- Structural matcher: token extraction, Jaccard similarity, plagiarism detection
- Dependency validator: breaking change detection, signature compatibility

### Integration Tests
- Full indexing workflow
- Code generation workflow (Legacy + Greenfield modes)
- Retry logic with explanations
- Incremental index updates

### Test Repositories
- Simple (10 files, 50 functions)
- Medium (50 files, 200 functions)
- Complex (100+ files, 500+ functions)

---

## CLI Usage

```bash
# Index repository
context-agent index /path/to/repo

# Generate code (Legacy Mode)
context-agent generate \
  --request "Add email validation to user_service.py" \
  --target-file src/services/user_service.py \
  --mode legacy

# Generate code (Greenfield Mode)
context-agent generate \
  --request "Create new payment module" \
  --target-file src/services/payment.py \
  --mode greenfield

# Update index
context-agent update-index --files file1.py file2.py

# Search functions
context-agent search --query "email validation" --top-k 5
```

---

## Performance Targets

### Indexing
- Small repo (10 files): ~5 seconds
- Medium repo (50 files): ~30 seconds
- Large repo (500 files): ~5 minutes

### Query
- Vector search: <100ms
- Dependency traversal: <50ms
- Full validation: <500ms

### Memory
- Small repo: ~100MB
- Medium repo: ~500MB
- Large repo: ~2GB

---

## Extensibility

### Custom Components
- **Embedders**: Implement custom embedding interface
- **Validators**: Add custom validation logic to metric system
- **LLM Providers**: Implement custom LLM provider interface
- **Metrics**: Define custom metric calculations

---

## Key Refinements from Original Design

1. **Call Graph Addition**: Track function-level calls, not just imports
2. **Cumulative Subtask Memory**: Prevent duplication within same session
3. **Dynamic k-Retrieval**: Variable number of results based on relevance threshold
4. **Semantic Context in Plagiarism Detection**: Avoid false positives on common patterns
5. **Incremental Index Updates**: Efficiently update when files change
6. **Explanation Layer**: Guide agent toward correct approach on validation failure
7. **Dependency Validation**: Check for breaking changes in dependent files

---

## Critical Success Factors

1. **Accurate AST Parsing**: Must handle all Python syntax correctly
2. **Quality Embeddings**: Jina Code V2 must capture semantic similarity well
3. **Balanced Thresholds**: 40% reuse / 85% structural similarity must work in practice
4. **Fast Vector Search**: ChromaDB HNSW index must be performant
5. **Clear Explanations**: Failed validations must guide agent effectively
6. **Robust Call Resolution**: Must handle imports, aliases, dynamic calls correctly

---

## Future Enhancements

### Short-term
- Multi-language support (JavaScript, TypeScript, Java)
- IDE integration (VS Code extension)
- Web UI

### Medium-term
- Cross-repository search
- Semantic code search with natural language
- Automated refactoring suggestions

### Long-term
- AI-powered architecture analysis
- Automated test generation
- Documentation generation
- Learning from user corrections

---

## Conclusion

This architecture provides a complete blueprint for building a Context-Aware Code Generation Agent. The system enforces deterministic code reuse through:

1. **Offline indexing** with AST analysis and vector embeddings
2. **Efficient context management** with rolling subtask windows
3. **Dual-phase verification** combining namespace checking and structural similarity
4. **Flexible modes** for different use cases (Legacy vs Greenfield)

