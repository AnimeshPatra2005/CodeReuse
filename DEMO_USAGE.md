# Demo Usage Guide - Context-Aware Code Generation Agent

Complete guide for running the demo and recording your hackathon video.

## 🎯 Overview

This demo showcases the **Context-Aware Code Generation Agent** with:
- ✅ **Automatic GitHub cloning** - Just paste a URL!
- ✅ **Beautiful terminal UI** - Professional visualizations
- ✅ **Live progress tracking** - See indexing in real-time
- ✅ **Quality metrics** - Namespace reuse & structural validation
- ✅ **Automatic refactoring** - Iterates until quality threshold met

## 📋 Prerequisites

### 1. Install Dependencies

```bash
# Install all required packages including Rich for beautiful UI
pip install -r requirements.txt
```

### 2. Set API Key

```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="your-gemini-api-key-here"

# Linux/Mac
export GEMINI_API_KEY="your-gemini-api-key-here"
```

### 3. Prepare Demo Repository

#### Option A: Use the Provided Demo Repository

```bash
cd demo_repository
git init
git add .
git commit -m "Initial commit: E-commerce demo application"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/demo-ecommerce.git
git push -u origin main
```

#### Option B: Use Your Own Repository

Any Python repository with multiple files and functions will work!

## 🚀 Running the Demo

### Basic Usage

```bash
python demo.py \
  --repo https://github.com/YOUR_USERNAME/demo-ecommerce \
  --query "Add email validation to user registration" \
  --target-file services/user_service.py
```

### Command-Line Arguments

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `--repo` | ✅ Yes | GitHub URL or local path | `https://github.com/user/repo` |
| `--query` | ✅ Yes | What you want to build | `"Add validation function"` |
| `--target-file` | ✅ Yes | Target file (relative to repo) | `services/user.py` |
| `--mode` | ❌ No | Agent mode (legacy/greenfield) | `legacy` (default) |
| `--max-iterations` | ❌ No | Max refactor iterations | `3` (default) |

## 🎬 Demo Scenarios for Video

### Scenario 1: User Registration with Validation ⭐ RECOMMENDED

**Best for showcasing code reuse!**

```bash
python demo.py \
  --repo https://github.com/YOUR_USERNAME/demo-ecommerce \
  --query "Create a register_user_with_validation function that validates email, username, and password before creating the user" \
  --target-file services/user_service.py \
  --max-iterations 3
```

**Why this is great:**
- Will reuse 5+ existing validation functions
- Shows high namespace reuse score (60-80%)
- Demonstrates automatic refactoring if needed
- Clear before/after comparison

**Expected reused functions:**
- `validate_email()` from validators.py
- `validate_username()` from validators.py  
- `validate_password()` from validators.py
- `check_email_format()` from email.py
- `sanitize_input()` from validators.py
- `create_user()` from user_service.py

### Scenario 2: Order Summary with Formatting

```bash
python demo.py \
  --repo https://github.com/YOUR_USERNAME/demo-ecommerce \
  --query "Create a function to generate a formatted order summary with currency and date formatting" \
  --target-file services/order_service.py
```

**Expected reused functions:**
- `format_currency()` from formatters.py
- `format_date()` from formatters.py
- `calculate_order_total()` from order_service.py

### Scenario 3: Product Search with Email

```bash
python demo.py \
  --repo https://github.com/YOUR_USERNAME/demo-ecommerce \
  --query "Add a function to search products and send results via email notification" \
  --target-file services/product_service.py
```

**Expected reused functions:**
- `search_products()` from product_service.py
- `create_email_template()` from email.py
- `format_email_list()` from email.py

## 📺 Recording Your Video

### Terminal Setup

1. **Size:** 120 columns x 40 rows
   ```bash
   # Check current size
   $Host.UI.RawUI.WindowSize
   
   # Set size (PowerShell)
   $Host.UI.RawUI.WindowSize = New-Object System.Management.Automation.Host.Size(120, 40)
   ```

2. **Theme:** Use a dark theme for better contrast
3. **Font:** Monospace, size 14-16 for readability
4. **Clear history:** `cls` or `clear` before recording

### Recording Flow (2-3 minutes)

#### Part 1: Introduction (15 seconds)
- Show welcome screen with ASCII art
- Briefly explain the problem: "AI code generation often duplicates code"
- Introduce solution: "Our agent enforces deterministic code reuse"

#### Part 2: GitHub URL Automation (10 seconds)
- **Key moment!** Paste GitHub URL
- Emphasize: "Just paste any GitHub URL - automatic cloning!"
- Show validation message

#### Part 3: Indexing (30 seconds)
- Let progress bars run (can speed up in editing)
- Highlight statistics:
  - "57 functions indexed"
  - "156 import statements analyzed"
  - "412 dependency edges mapped"
- Show completion message

#### Part 4: Code Generation (45 seconds)
- Show the query clearly
- Display context gathering (similar functions found)
- Show generated code with syntax highlighting
- **Key moment:** Score dashboard
  - Point out namespace reuse score
  - Explain threshold (40%)
  - Show structural similarity check

#### Part 5: Refactoring (30 seconds - if triggered)
- Show warning: "Quality below threshold"
- Display before/after comparison
- Highlight score improvement
- Show success message

#### Part 6: Summary (15 seconds)
- Final statistics
- List of reused functions
- Key achievements
- End with tagline: "Deterministic code reuse with AI"

### Narration Script

```
[Welcome Screen]
"Traditional AI code generation often duplicates existing code, 
leading to maintenance nightmares."

[GitHub URL]
"With our Context-Aware Agent, just paste any GitHub URL..."

[Cloning]
"...and it automatically clones and indexes the entire codebase."

[Indexing Progress]
"Using AST parsing and vector embeddings, it maps all 57 functions
and their dependencies in seconds."

[Query]
"Now, let's ask it to add email validation to user registration."

[Context Gathering]
"The agent finds 5 similar functions in the existing codebase..."

[Code Generation]
"...and generates new code that reuses them!"

[Score Dashboard]
"Our dual-phase validation ensures quality:
- 75% namespace reuse - excellent!
- Structural similarity check - passed!
- Overall quality: 82%"

[Summary]
"The agent enforced code reuse, prevented duplication,
and validated dependencies automatically.

This is deterministic code reuse with AI."
```

### Video Editing Tips

1. **Speed up slow parts:**
   - Indexing progress (2x speed)
   - Code generation (1.5x speed)

2. **Add text overlays:**
   - "Automatic GitHub Cloning"
   - "AST-Based Analysis"
   - "Vector Similarity Search"
   - "Dual-Phase Validation"
   - "75% Code Reuse Achieved!"

3. **Zoom in on:**
   - Score dashboard (key innovation!)
   - Reused functions list
   - Before/after comparison

4. **Background music:**
   - Subtle, tech-focused
   - Not distracting
   - Fade out for narration

5. **Final length:** 2-3 minutes ideal for hackathons

## 🎨 What Makes This Demo Special

### Visual Highlights

1. **ASCII Art Logo** - Professional branding
2. **Live Progress Bars** - Shows real-time indexing
3. **Color-Coded Scores** - Green (good), Yellow (warning), Red (fail)
4. **Syntax Highlighting** - Beautiful code display
5. **Side-by-Side Comparison** - Clear before/after
6. **Statistics Panels** - Professional data presentation

### Technical Highlights

1. **GitHub Integration** - Automatic cloning
2. **AST Analysis** - Deep code understanding
3. **Vector Search** - Intelligent function matching
4. **Namespace Validation** - Enforces code reuse
5. **Structural Matching** - Prevents plagiarism
6. **Automatic Refactoring** - Quality-driven iteration

## 🐛 Troubleshooting

### Issue: "GEMINI_API_KEY not set"
**Solution:** Set the environment variable before running

### Issue: "Git is not installed"
**Solution:** Install Git from https://git-scm.com/

### Issue: "Repository cloning failed"
**Solution:** 
- Check GitHub URL is correct
- Ensure repository is public
- Check internet connection

### Issue: "Rich not displaying colors"
**Solution:** 
- Use a terminal that supports ANSI colors
- Try Windows Terminal instead of CMD
- Update terminal settings

### Issue: "Indexing takes too long"
**Solution:** Use the provided demo_repository (smaller, optimized for demo)

## 📊 Expected Results

For the recommended scenario (user registration with validation):

```
✅ Namespace Reuse Score: 66-75%
✅ Structural Similarity: <30%
✅ Overall Quality: 75-85%
✅ Functions Reused: 5-6
✅ Status: SUCCESS
```

## 🎯 Key Talking Points for Judges

1. **Novel Approach:** "We enforce deterministic code reuse through dual-phase validation"
2. **Automation:** "Just paste a GitHub URL - everything else is automatic"
3. **Quality Metrics:** "Namespace reuse score ensures maximum code reuse"
4. **Iteration:** "Automatic refactoring until quality threshold is met"
5. **Transparency:** "Beautiful visualizations show exactly what's happening"

## 📝 Post-Demo Checklist

- [ ] Video recorded (2-3 minutes)
- [ ] Audio clear and professional
- [ ] Key features highlighted
- [ ] Scores visible and explained
- [ ] Before/after comparison shown
- [ ] Summary statistics displayed
- [ ] Edited with text overlays
- [ ] Background music added
- [ ] Final review completed
- [ ] Uploaded to submission platform

## 🚀 Ready to Record!

You now have everything you need to create an impressive demo video. The combination of:
- Beautiful terminal UI
- Automatic GitHub integration
- Live progress tracking
- Quality metrics visualization
- Professional summary

...will make your hackathon submission stand out!

**Good luck! 🎉**

---

For questions or issues, check the logs at `./logs/demo.log`