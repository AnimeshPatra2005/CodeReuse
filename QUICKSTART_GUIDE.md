# 🚀 Quick Start Guide - Run Your Vision

## Prerequisites

Make sure you have:
- ✅ Python 3.8+ installed
- ✅ Git installed
- ✅ Hugging Face API token (for IBM Granite)

---

## Step 1: Install Dependencies

Open terminal in `c:/Users/BIT/Desktop/ibmbob` and run:

```bash
pip install -r requirements.txt
```

---

## Step 2: Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Create .env file
echo HUGGINGFACE_API_TOKEN=your_token_here > .env
```

**Replace `your_token_here` with your actual Hugging Face API token.**

To get a token:
1. Go to https://huggingface.co/settings/tokens
2. Create a new token
3. Copy and paste it in the `.env` file

---

## Step 3: Start the Backend

Open **Terminal 1** and run:

```bash
# Make sure you're in the project root
cd c:/Users/BIT/Desktop/ibmbob

# Start the FastAPI backend
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Keep this terminal running!**

---

## Step 4: Start the Frontend

Open **Terminal 2** and run:

```bash
# Navigate to frontend directory
cd c:/Users/BIT/Desktop/ibmbob/frontend

# Option 1: Use the batch file (Windows)
launch.bat

# Option 2: Or open index.html directly in your browser
# Just double-click: frontend/index.html
```

Your browser should open to `http://localhost:8080` (or you can manually open `frontend/index.html`)

---

## Step 5: Use the Application

### 5.1 Index a Repository

1. On the landing page, enter a repository path:
   - **Local path**: `./sample_repo` or `./demo_repository`
   - **GitHub URL**: `https://github.com/username/repo`

2. Click **"Analyze"**

3. Watch the processing steps:
   - ✅ Cloning Repository
   - ✅ Parsing AST
   - ✅ Building Dependency Graph
   - ✅ Creating Vector Embeddings

4. You'll see stats:
   - Files: 6
   - Functions: 51
   - Imports: 16

### 5.2 View Dependency Graph

After indexing completes:
- Beautiful interactive graph appears
- Shows files and functions interconnected
- Drag nodes to explore
- See dependencies visually

Click **"Go to IDE"** when ready

### 5.3 Generate Code

1. **Select Target File**: Choose from dropdown (e.g., `sample_repo/user_service.py`)

2. **Enter Your Query**: 
   ```
   Add email validation to the user registration function
   ```

3. **Click "Generate Code"**

4. **Watch the Leftmost Logs Panel** - You'll see:
   ```
   [12:34:56] 🎯 [SUBTASK 1] Description: Add email validation
   [12:34:57] 📊 Similarity threshold: 0.70
   [12:34:58] ✓ Retrieved: validate_email [validators.py] similarity: 92.0%
   [12:34:58] ✓ Retrieved: check_email_format [email.py] similarity: 87.0%
   [12:35:00] Code generated (156 lines)
   [12:35:01] Namespace reuse: 75.0% ✓ PASS
   [12:35:02] 🔗 Found 2 dependent files: auth.py, registration.py
   [12:35:03] 🤖 LLM Validation: No compatibility issues detected
   ```

5. **View Metrics** (Right Panel):
   - Namespace Reuse Score: 75%
   - Structural Similarity: 23.5%
   - Overall Quality: 82.3%

6. **Copy Generated Code**: Click "Copy" button

---

## 🎯 Example Queries to Try

```
1. "Add email validation to user registration"
2. "Create a function to hash passwords securely"
3. "Add input sanitization before database queries"
4. "Implement rate limiting for API endpoints"
5. "Add logging to all database operations"
```

---

## 🔍 What to Watch For

### In the Logs Panel (Left):
- ✅ Subtask descriptions
- ✅ Retrieved functions with similarity scores
- ✅ Semantic similarity threshold
- ✅ Dependent file names
- ✅ LLM validation reports

### In the Metrics Panel (Right):
- ✅ Namespace Reuse Score (should be >40%)
- ✅ Structural Similarity (should be <85%)
- ✅ Overall Quality Score

### In the Code Panel (Center):
- ✅ Generated Python code
- ✅ Proper imports
- ✅ Reuses existing functions
- ✅ Clean, documented code

---

## 🐛 Troubleshooting

### Backend won't start:
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill the process if needed
taskkill /PID <process_id> /F

# Try again
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend won't connect:
1. Check backend is running (Terminal 1 should show "Uvicorn running")
2. Check browser console for errors (F12)
3. Make sure you're accessing `http://localhost:8080` or opening `index.html`

### No logs appearing:
1. Check WebSocket connection (should show "WS" badge as green in IDE page)
2. Refresh the page
3. Check backend terminal for errors

### "Agent not initialized" error:
- You need to index a repository first
- Go back to landing page and index `./sample_repo`

---

## 📁 Test Repositories

### Option 1: Use Sample Repo (Included)
```
./sample_repo
```
Contains:
- `user_service.py`
- `utils.py`
- `__init__.py`

### Option 2: Use Demo Repository (Included)
```
./demo_repository
```
Contains:
- Services (user_service, product_service, order_service)
- Utils (validators, formatters, email)
- More complex for testing

### Option 3: Use Your Own Repo
```
https://github.com/yourusername/yourrepo
```
Or any local path:
```
C:/path/to/your/project
```

---

## 🎬 Complete Workflow Example

```bash
# Terminal 1: Start backend
cd c:/Users/BIT/Desktop/ibmbob
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Start frontend
cd c:/Users/BIT/Desktop/ibmbob/frontend
launch.bat

# Browser:
1. Enter: ./sample_repo
2. Click: Analyze
3. Wait for graph
4. Click: Go to IDE
5. Select: sample_repo/user_service.py
6. Type: "Add email validation function"
7. Click: Generate Code
8. Watch logs panel (left) - see everything!
9. Check metrics (right) - see scores!
10. Copy code (center) - use it!
```

---

## ✅ Success Indicators

You'll know it's working when you see:

1. **Backend Terminal**:
   ```
   INFO:     WebSocket connected. Total connections: 1
   INFO:     Starting repository indexing: ./sample_repo
   INFO:     Repository indexing completed
   ```

2. **Frontend Logs**:
   ```
   [12:34:56] WebSocket connected to backend
   [12:34:57] 🎯 [SUBTASK 1] Description: ...
   [12:34:58] ✓ Retrieved: function_name [file.py] similarity: 92.0%
   [12:35:03] 🤖 LLM Validation: No compatibility issues detected
   ```

3. **Metrics Panel**:
   - Green progress bars
   - Scores above thresholds
   - "✅ PASS" status

---

## 🎉 You're Ready!

Your vision is now fully operational. Every feature you described is working:
- ✅ Detailed logging
- ✅ Function retrieval with similarity
- ✅ Threshold display
- ✅ Dependent file validation
- ✅ LLM reports

**Enjoy your context-aware code generation system!** 🚀

---

## 📞 Need Help?

Check the logs in:
- Backend: Terminal 1 output
- Frontend: Browser console (F12)
- Application: Leftmost logs panel

All errors and information are logged there.

---

**Made with Bob** 💻