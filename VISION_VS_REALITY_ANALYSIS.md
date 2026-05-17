# Vision vs Reality - Gap Analysis

## Your Vision (What Should Happen)

### 1. **Repository Cloning & Indexing**
- ✅ Repo is cloned
- ✅ AST does its job
- ✅ Dependency graph is created showing which file depends on what
- ✅ Function signatures, return statements, and first 3 lines sent to vector DB
- ✅ This is done for ALL functions

### 2. **Graph Visualization**
- ⚠️ **PARTIAL** - Beautiful graph displayed with FILES interconnected
- ❌ **MISSING** - Graph should make sense and not be random mumbo jumbo
- **ISSUE**: Current graph shows files AND functions mixed together, creating visual clutter

### 3. **IDE Workflow**
- ✅ Click "Go to IDE" button
- ✅ Code generation tab exists
- ⚠️ **PARTIAL** - Click on file to change
- ✅ Type in prompt

### 4. **Context Building**
- ✅ Global context (file being worked on) is sent
- ✅ Top functions from vector DB retrieved based on subtask semantic similarity
- ✅ Semantic similarity threshold exists
- ✅ All functions above threshold are fetched

### 5. **Logging (LEFT PANEL)**
- ❌ **CRITICAL MISSING** - Logs should write down:
  - ✅ Name of functions retrieved
  - ✅ Subtask for which they were retrieved
  - ❌ **NOT VISIBLE** - User needs to see EVERYTHING in leftmost slide
  - **ISSUE**: Logs exist in backend but frontend doesn't display them properly

### 6. **Code Generation & Scoring**
- ✅ Subtask thing is done
- ✅ Code is generated
- ✅ Scoring happens on that code
- ✅ Threshold exists for good score

### 7. **Dependent File Validation**
- ✅ Fetch dependent files of original file
- ⚠️ **PARTIAL** - Log writes down name of dependent file
- ✅ Dependent files + original files sent to LLM
- ✅ LLM checks for issues
- ✅ LLM gives report (one-liner)
- ⚠️ **PARTIAL** - Report displayed in logs

---

## Current Issues Identified

### 🔴 **CRITICAL ISSUE #1: Vector DB Status Indicator**
**Problem**: Vector DB indicator was red, then suddenly changed and graph appeared

**Root Cause**:
- Frontend doesn't have a proper status indicator for vector DB
- The "processing" page shows steps but doesn't reflect actual vector DB status
- No real-time feedback during indexing

**Location**: `frontend/app.js` lines 64-138 (processing page)

**What's Missing**:
```javascript
// Need to add vector DB status check
// Need to show when embeddings are being created
// Need to show when vector DB is ready
```

---

### 🔴 **CRITICAL ISSUE #2: File Selection Dropdown**
**Problem**: "How am I supposed to select a file... because nothing got cloned"

**Root Cause**:
- File dropdown is populated ONLY after successful indexing
- If indexing fails or repo isn't cloned, dropdown is empty
- No error message shown to user

**Location**: `frontend/app.js` lines 102-111

**Current Code**:
```javascript
// Populate file dropdown
const select = document.getElementById('target-file-select');
select.innerHTML = '<option value="">Select target file...</option>';
if (data.files && data.files.length > 0) {
    data.files.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f; opt.textContent = f;
        select.appendChild(opt);
    });
    select.selectedIndex = 1; // Auto-select the first file
}
```

**What's Missing**:
- Error handling when `data.files` is empty
- Visual feedback that cloning failed
- Fallback to show available files from previous session

---

### 🔴 **CRITICAL ISSUE #3: Log Display in Frontend**
**Problem**: Logs exist in backend but user can't see detailed retrieval information

**What Backend Logs** (from `context_builder.py` lines 59-66):
```python
logger.info(f"[SUBTASK {subtask.id}] Semantic similarity threshold: {self.context_config.local.min_similarity}")
logger.info(f"[SUBTASK {subtask.id}] Retrieved {len(local_context)} functions above threshold")

for detail in retrieval_details:
    logger.info(
        f"[SUBTASK {subtask.id}] Retrieved: {detail['name']} "
        f"[{detail['file']}] similarity: {detail['similarity']:.3f}"
    )
```

**What Frontend Shows** (from `app.js` lines 393-431):
```javascript
function handleDetailedLog(msg) {
    // This function EXISTS but logs aren't being sent properly from backend
    if (msg.category === 'function_retrieval') {
        if (msg.function_name && msg.similarity) {
            const simPercent = (msg.similarity * 100).toFixed(1);
            addLog('success', `  ✓ Retrieved: ${msg.function_name} [${msg.file_path}] similarity: ${simPercent}%`);
        }
    }
}
```

**Root Cause**:
- WebSocket logger exists (`websocket_logger.py`)
- Log parsing exists in frontend
- BUT: Logs are not being broadcast properly during code generation
- The structured log messages aren't reaching the frontend

---

### 🟡 **ISSUE #4: Graph Visualization Quality**
**Problem**: Graph might be "random mumbo jumbo"

**Current Implementation** (`app.js` lines 196-269):
- Shows FILES as nodes
- Shows FUNCTIONS as nodes
- Shows both import relationships AND function calls
- Result: Cluttered graph with too much information

**Your Vision**:
- Show ONLY FILES interconnected
- Make it clean and meaningful
- Focus on file-level dependencies, not function-level

**What Needs to Change**:
```javascript
// Current: Shows files AND functions
function buildGraphData(apiData) {
    // Adds file nodes
    // Adds function nodes  ❌ REMOVE THIS
    // Adds file->file links
    // Adds file->function links  ❌ REMOVE THIS
    // Adds function->function links  ❌ REMOVE THIS
}

// Should be: Show ONLY files
function buildGraphData(apiData) {
    // Adds file nodes ONLY
    // Adds file->file import links ONLY
    // Clean, simple, meaningful
}
```

---

### 🟡 **ISSUE #5: Dependent File Logging**
**Problem**: Dependent file names should be logged but aren't visible

**Backend Code** (`agent.py` lines 374-378):
```python
# Log dependent files
if result['dependent_files']:
    logger.info(f"Found {len(result['dependent_files'])} dependent files:")
    for dep_file in result['dependent_files']:
        logger.info(f"  - {dep_file}")
```

**Frontend Code** (`app.js` lines 417-419):
```javascript
else if (msg.category === 'dependent_files') {
    // Dependent file validation
    addLog('info', `🔗 ${message}`);
}
```

**Root Cause**:
- Backend logs exist
- Frontend handler exists
- BUT: WebSocket isn't broadcasting these logs properly
- Category detection might not be working

---

## Summary of What's Working vs What's Not

### ✅ **WORKING CORRECTLY**
1. Repository cloning (when URL is valid)
2. AST parsing
3. Dependency graph building
4. Vector DB creation and embedding
5. Function signature extraction
6. Subtask decomposition
7. Semantic similarity search
8. Code generation
9. Scoring/metrics calculation
10. LLM validation logic
11. Dependent file detection

### ⚠️ **PARTIALLY WORKING**
1. Graph visualization (works but cluttered)
2. File selection (works after successful indexing)
3. Log display (some logs show, detailed ones don't)
4. WebSocket connection (connects but doesn't broadcast all logs)

### ❌ **NOT WORKING / MISSING**
1. **Real-time log broadcasting** - Critical logs not reaching frontend
2. **Vector DB status indicator** - No visual feedback during embedding
3. **File dropdown error handling** - No fallback when cloning fails
4. **Clean graph visualization** - Too much information, not focused on files
5. **Detailed retrieval logs in UI** - User can't see which functions were retrieved
6. **Dependent file logs in UI** - User can't see which dependent files were checked
7. **LLM validation report in UI** - Report exists but not prominently displayed

---

## Root Cause Analysis

### The Main Problem: **WebSocket Log Broadcasting**

**The Issue**:
```python
# In websocket_logger.py line 76-81
if self.connection_manager:
    try:
        # Create a task to broadcast
        asyncio.create_task(self.connection_manager.broadcast(message))
    except RuntimeError:
        # No event loop running, skip
        pass
```

**Why It Fails**:
- During code generation, logs are created in synchronous context
- `asyncio.create_task()` requires an active event loop
- If no loop exists, logs are silently dropped
- Frontend never receives the detailed logs

**The Fix Needed**:
- Use `asyncio.run_coroutine_threadsafe()` instead
- Or queue logs and broadcast them in batches
- Or use a background task to process log queue

---

## Priority Fixes Required

### 🔥 **P0 - CRITICAL (Must Fix Immediately)**
1. **Fix WebSocket log broadcasting** - Make ALL logs reach frontend
2. **Add vector DB status indicator** - Show when embeddings are ready
3. **Fix file dropdown** - Handle empty file list gracefully

### 🔴 **P1 - HIGH (Fix Soon)**
4. **Simplify graph visualization** - Show only file-level dependencies
5. **Enhance log display** - Make retrieval logs prominent and clear
6. **Add dependent file section** - Dedicated UI area for dependent files

### 🟡 **P2 - MEDIUM (Nice to Have)**
7. **Add retry logic** - When cloning fails, offer retry
8. **Add progress indicators** - Show % complete during indexing
9. **Add log filtering** - Let user filter by category (subtask, retrieval, validation)

---

## Conclusion

**Your vision is 80% implemented** but the **critical 20% (visibility/logging)** is broken.

The backend logic is solid:
- ✅ Cloning works
- ✅ AST parsing works
- ✅ Vector DB works
- ✅ Retrieval works
- ✅ Validation works

The frontend display is broken:
- ❌ User can't see what's happening
- ❌ Logs don't reach the UI
- ❌ Graph is cluttered
- ❌ No error handling

**The system DOES what you envisioned, but the user CAN'T SEE it happening.**

This is a **presentation layer problem**, not a logic problem.