# Context-Aware Code Generation Agent

A production-ready AI-powered code generation system that **enforces deterministic code reuse** through AST analysis, vector similarity search, and structural verification. Prevents code duplication by ensuring AI agents leverage existing utilities instead of creating redundant implementations.

## 🎯 Core Innovation

**Dual-phase verification** (namespace checking + structural similarity) with rolling subtask context management ensures generated code reuses existing functions instead of duplicating logic.

## ✨ Key Features

- **🔍 Semantic Code Search**: ChromaDB + Jina embeddings for finding similar functions
- **📊 Code Reuse Enforcement**: Minimum 40% reuse score validation
- **🚫 Plagiarism Detection**: AST-based structural similarity checking (85% threshold)
- **🔄 Dependency Tracking**: Import/call graph analysis with breaking change detection
- **🤖 Intelligent Task Decomposition**: Gemini-powered subtask breakdown (2-5 subtasks)
- **💡 Explanatory Feedback**: Detailed failure explanations guide regeneration
- **🔁 Automatic Retry**: Up to 3 retries with explanations
- **🎭 Dual Modes**: Legacy (enforces reuse) vs Greenfield (no validation)

## 🏗️ Architecture

```
Repository → Indexing → Vector DB + Dependency Graph
                              ↓
User Request → Task Decomposition → Subtasks
                              ↓
For each subtask:
  Global Context + Local Context (similar functions)
                              ↓
  LLM Code Generation (Gemini)
                              ↓
  Metric Validation (Legacy Mode)
                              ↓
  Update Subtask Memory → Next Subtask
                              ↓
Final Code → Dependency Validation → Output
```

## 📦 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- Gemini API Key

### Backend Setup

```bash
# Clone repository
git clone <your-repo-url>
cd context-aware-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Frontend Setup (Optional)

```bash
cd frontend
npm install
npm run dev
```

## 🚀 Quick Start

### 1. Index Your Repository

```bash
# Using CLI
python cli.py index ./path/to/your/repo

# Using API
curl -X POST "http://localhost:8000/index/repository" \
  -H "Content-Type: application/json" \
  -d '{"repository_path": "./path/to/repo"}'
```

### 2. Generate Code

```bash
# Using CLI
python cli.py generate \
  "Add email validation to user registration" \
  --target-file src/services/user_service.py \
  --mode legacy \
  --output generated_code.py

# Using API
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Add email validation",
    "target_file": "src/services/user_service.py",
    "mode": "legacy"
  }'
```

### 3. Search Functions

```bash
# Using CLI
python cli.py search "email validation" --top-k 5

# Using API
curl "http://localhost:8000/search/functions?query=email+validation&top_k=5"
```

## 🖥️ API Server

### Start Server

```bash
# Development
python -m src.api.main

# Production
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### API Endpoints

- `POST /index/repository` - Index a repository
- `POST /generate` - Generate code
- `GET /search/functions` - Search for similar functions
- `GET /stats` - Get indexing statistics
- `GET /config` - Get current configuration
- `WS /ws` - WebSocket for real-time updates

### WebSocket Events

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws');

// Subscribe to events
ws.send(JSON.stringify({ type: 'subscribe' }));

// Receive events
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.type: indexing_started, indexing_completed, generation_started, etc.
};
```

## 📊 Validation Metrics

### Namespace Reuse Score

```
reuse_score = |called_functions ∩ repo_functions| / |called_functions|
```

- **Threshold**: 40% minimum
- **Purpose**: Ensure code calls existing functions

### Structural Similarity

```
jaccard_similarity = |tokens1 ∩ tokens2| / |tokens1 ∪ tokens2|
```

- **Threshold**: 85% maximum
- **Purpose**: Detect code plagiarism (copying logic instead of calling)

### Dependency Validation

- Checks for breaking changes in dependent files
- Validates signature compatibility
- Reports import resolution issues

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
agent:
  mode: "legacy"  # or "greenfield"
  llm:
    model: "gemini-1.5-flash"
    temperature: 0.2

metrics:
  namespace:
    min_reuse_score: 0.4
  structural:
    max_similarity: 0.85
  retry:
    max_retries: 3

context:
  local:
    min_similarity: 0.7
    max_k: 5
```

## 📁 Project Structure

```
context-aware-agent/
├── src/
│   ├── indexing/          # AST parsing, vector DB, dependency graphs
│   ├── agent/             # Task decomposition, context building, orchestration
│   ├── metrics/           # Validation (namespace, structural, dependency)
│   ├── models/            # Pydantic data models
│   ├── utils/             # Config, logging
│   └── api/               # FastAPI server
├── frontend/              # React frontend (optional)
├── tests/                 # Unit and integration tests
├── cli.py                 # Command-line interface
├── config.yaml            # Configuration
└── requirements.txt       # Python dependencies
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_ast_parser.py
```

## 🎨 Frontend (React + Tailwind)

The frontend provides:

- **Repository Upload**: Drag-and-drop or file browser
- **Real-time Indexing**: Progress bar with file count
- **Code Generation Interface**: Text input with mode selection
- **Split View**: Generated code | Similar functions found
- **Metrics Dashboard**: Reuse scores, similarity graphs, violations
- **WebSocket Updates**: Live progress notifications

### Frontend Development

```bash
cd frontend
npm install
npm run dev  # Development server
npm run build  # Production build
```

## 📈 Performance

### Indexing Speed

- Small repo (10 files): ~5 seconds
- Medium repo (50 files): ~30 seconds
- Large repo (500 files): ~5 minutes

### Query Performance

- Vector search: <100ms
- Dependency traversal: <50ms
- Full validation: <500ms

## 🔧 Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not set"**
   - Copy `.env.example` to `.env`
   - Add your Gemini API key

2. **"Repository not indexed"**
   - Run `python cli.py index ./path/to/repo` first

3. **Import errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

4. **ChromaDB errors**
   - Delete `./chroma_db` directory
   - Re-index repository

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **ChromaDB** for vector database
- **Jina AI** for code embeddings
- **Google Gemini** for LLM capabilities
- **FastAPI** for API framework

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built for hackathons, ready for production** 🚀