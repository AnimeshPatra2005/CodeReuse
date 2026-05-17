# IBM Granite Integration Guide

## Overview

This project now uses **IBM Granite** models for code generation instead of Google Gemini. IBM Granite is an open-source family of LLMs specifically designed for code generation and understanding.

## Why IBM Granite?

- ✅ **Open Source**: No vendor lock-in
- ✅ **Code-Specialized**: Trained specifically for code tasks
- ✅ **Free to Use**: Via Hugging Face Inference API
- ✅ **IBM Product**: Aligns with IBM-only requirement
- ✅ **Production Ready**: Enterprise-grade quality

## Setup Instructions

### 1. Get Hugging Face API Token

1. Go to [Hugging Face](https://huggingface.co/)
2. Create a free account (no credit card required)
3. Go to Settings → Access Tokens: https://huggingface.co/settings/tokens
4. Create a new token with "Read" permissions
5. Copy the token

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Copy from example
cp .env.example .env

# Edit .env and add your token
HUGGINGFACE_API_TOKEN=hf_your_token_here
```

### 3. Install Dependencies

```bash
# Activate your virtual environment
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source venv/bin/activate  # Linux/Mac

# Install/upgrade dependencies
pip install --upgrade huggingface-hub transformers accelerate
```

### 4. Test the Setup

```bash
python demo.py --repo ./demo_repository --query "Add email validation" --target-file services/user_service.py
```

## Models Used

### Code Generation: IBM Granite 3B Code Instruct
- **Model**: `ibm-granite/granite-3b-code-instruct`
- **Size**: 3 billion parameters
- **Purpose**: Code generation with instruction following
- **Context**: 2048 tokens
- **Speed**: Fast inference via HF API

### Embeddings: Sentence Transformers
- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Size**: 384 dimensions
- **Purpose**: Code similarity search
- **Speed**: Very fast, works well with code

## Architecture Changes

### Before (Gemini)
```
User Query → Gemini API → Generated Code
```

### After (IBM Granite)
```
User Query → Context Builder → IBM Granite (HF API) → Generated Code
                ↓
         Global Context (target file)
         Local Context (similar functions)
         System Prompt (senior architect persona)
```

## Key Features

### 1. Proper Context Structure
- **Global Context**: Full target file content
- **Local Context**: Top-5 most similar existing functions
- **System Prompt**: "Senior architect who values code reuse"

### 2. Code Reuse Enforcement
The system prompt explicitly instructs Granite to:
- Reuse existing functions instead of reimplementing
- Import and call existing utilities
- Minimize new code (less code = less maintenance)

### 3. Simplified for MVP
- No subtask decomposition (single task generation)
- Direct code generation with full context
- Faster iteration for demo purposes

## Configuration

Edit `config.yaml`:

```yaml
agent:
  mode: "legacy"  # or "greenfield"
  llm:
    provider: "huggingface"
    model: "ibm-granite/granite-3b-code-instruct"
    temperature: 0.2
    max_tokens: 2048
    use_local: false  # Set true for local inference
  subtask:
    enabled: false  # Simplified for MVP
  prompt:
    system_role: "You are a senior software architect who values code reuse..."
```

## Local Inference (Optional)

For production or offline use, you can run Granite locally:

### Requirements
- GPU with 8GB+ VRAM (for 3B model)
- 16GB+ RAM
- CUDA toolkit installed

### Setup
```bash
# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Download model (first run will cache it)
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('ibm-granite/granite-3b-code-instruct')"
```

### Configure
```yaml
# config.yaml
agent:
  llm:
    use_local: true  # Enable local inference
```

## Troubleshooting

### Error: "Hugging Face API token required"
- Make sure `.env` file exists with `HUGGINGFACE_API_TOKEN`
- Token must start with `hf_`
- Check token has "Read" permissions

### Error: "Model loading failed"
- Check internet connection
- Verify model name is correct
- Try: `huggingface-cli login` and enter token

### Slow Generation
- First request is slower (model loading)
- Subsequent requests are faster
- Consider local inference for production

### Rate Limiting
- Free tier: ~1000 requests/day
- Upgrade to Pro for more: https://huggingface.co/pricing
- Or use local inference (unlimited)

## Comparison: Gemini vs Granite

| Feature | Gemini | IBM Granite |
|---------|--------|-------------|
| **Cost** | Paid API | Free (HF) / Local |
| **Vendor** | Google | IBM (Open Source) |
| **Code Quality** | Excellent | Very Good |
| **Speed** | Fast | Fast (API) / Faster (Local) |
| **Context** | 32K tokens | 2K tokens |
| **Offline** | No | Yes (local) |
| **Enterprise** | Yes | Yes |

## Next Steps

1. ✅ Test with demo repository
2. ✅ Verify code generation quality
3. ✅ Check metric validation works
4. ⏭️ Fine-tune prompts for better reuse
5. ⏭️ Consider local deployment for production
6. ⏭️ Explore larger Granite models (8B, 20B)

## Resources

- [IBM Granite Models](https://huggingface.co/ibm-granite)
- [Granite 3B Code Instruct](https://huggingface.co/ibm-granite/granite-3b-code-instruct)
- [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index)
- [IBM watsonx.ai](https://www.ibm.com/products/watsonx-ai) (Enterprise option)

## Support

For issues or questions:
1. Check this guide first
2. Review logs in `./logs/agent.log`
3. Test with simple queries first
4. Verify API token is valid

---

**Made with IBM Granite 🪨**