# Setup Guide - Context-Aware Code Generation Agent

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
# Get key from: https://makersuite.google.com/app/apikey
```

Your `.env` should look like:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 3. Run Quick Start Demo

```bash
python quickstart.py
```

This will:
- Index the sample repository
- Generate code with validation
- Show metrics and results
- Save generated code to file

## Detailed Setup

### Option 1: CLI Usage

```bash
# 1. Index your repository
python cli.py index ./path/to/your/repo

# 2. Generate code
python cli.py generate \
  "Add password hashing function" \
  --target-file src/auth.py \
  --mode legacy \
  --output generated.py

# 3. Search for functions
python cli.py search "email validation" --top-k 5

# 4. View statistics
python cli.py stats
```

### Option 2: API Server

```bash
# Start server
python -m src.api.main

# Server runs on http://localhost:8000
# API docs: http://localhost:8000/docs
```

#### API Examples

**Index Repository:**
```bash
curl -X POST "http://localhost:8000/index/repository" \
  -H "Content-Type: application/json" \
  -d '{"repository_path": "./sample_repo"}'
```

**Generate Code:**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Add phone validation",
    "target_file": "sample_repo/utils.py",
    "mode": "legacy"
  }'
```

**Search Functions:**
```bash
curl "http://localhost:8000/search/functions?query=email&top_k=5"
```

### Option 3: Python API

```python
from src.indexing.indexer import Indexer
from src.agent.agent import Agent
from src.models.data_models import GenerationRequest, AgentMode
import os

# Index repository
indexer = Indexer(repository_path="./sample_repo")
metadata = indexer.index_repository()

# Initialize agent
agent = Agent(
    indexer.vector_db,
    indexer.graph_builder,
    os.getenv("GEMINI_API_KEY")
)

# Generate code
request = GenerationRequest(
    user_request="Add email validation",
    target_file="sample_repo/utils.py",
    mode=AgentMode.LEGACY
)

response = agent.generate_code(request)
print(response.generated_code)
```

## Configuration

Edit `config.yaml` to customize:

```yaml
agent:
  mode: "legacy"  # or "greenfield"
  llm:
    model: "gemini-1.5-flash"
    temperature: 0.2

metrics:
  namespace:
    min_reuse_score: 0.4  # 40% minimum reuse
  structural:
    max_similarity: 0.85  # 85% max similarity
  retry:
    max_retries: 3
```

## Troubleshooting

### Issue: "GEMINI_API_KEY not set"

**Solution:**
1. Create `.env` file from `.env.example`
2. Add your API key
3. Restart the application

### Issue: "Repository not indexed"

**Solution:**
```bash
python cli.py index ./path/to/repo
```

### Issue: Import errors

**Solution:**
```bash
# Ensure virtual environment is activated
pip install -r requirements.txt
```

### Issue: ChromaDB errors

**Solution:**
```bash
# Delete and re-index
rm -rf chroma_db
python cli.py index ./sample_repo
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_ast_parser.py -v
```

## Development

### Project Structure

```
context-aware-agent/
├── src/
│   ├── indexing/      # Repository analysis
│   ├── agent/         # Code generation
│   ├── metrics/       # Validation
│   ├── models/        # Data models
│   ├── utils/         # Utilities
│   └── api/           # FastAPI server
├── sample_repo/       # Test repository
├── tests/             # Test suite
├── cli.py             # CLI interface
├── quickstart.py      # Demo script
└── config.yaml        # Configuration
```

### Adding New Features

1. **New Validator:**
   - Create file in `src/metrics/`
   - Implement validation logic
   - Add to `MetricOrchestrator`

2. **New LLM Provider:**
   - Update `src/agent/agent.py`
   - Add provider configuration
   - Implement provider interface

3. **New Embedding Model:**
   - Update `src/indexing/vector_db.py`
   - Change model in `config.yaml`
   - Re-index repository

## Performance Optimization

### For Large Repositories

```yaml
# config.yaml
indexing:
  embedder:
    batch_size: 64  # Increase batch size

context:
  local:
    max_k: 3  # Reduce context size
```

### For Faster Generation

```yaml
agent:
  llm:
    model: "gemini-1.5-flash"  # Faster model
    temperature: 0.1  # More deterministic
```

## Production Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
export GEMINI_API_KEY=your_key
export LOG_LEVEL=INFO
export REPOSITORY_PATH=/path/to/repo
```

## Next Steps

1. ✅ Complete setup
2. 📚 Run quickstart demo
3. 🔍 Index your repository
4. 💻 Generate your first code
5. 📊 Review metrics
6. 🎨 Build frontend (optional)

## Support

- 📖 Read [README.md](README.md) for detailed documentation
- 🏗️ See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- 🐛 Report issues on GitHub
- 💬 Join discussions

---

**Ready to enforce code reuse!** 🚀