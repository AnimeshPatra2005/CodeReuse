# Enhanced CLI Demo - Terminal Output Mockup

## 1. Welcome Screen
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗ ██████╗ ██████╗ ███████╗     ██████╗ ███████╗██╗   ██╗███████╗   ║
║  ██╔════╝██╔═══██╗██╔══██╗██╔════╝     ██╔══██╗██╔════╝██║   ██║██╔════╝   ║
║  ██║     ██║   ██║██║  ██║█████╗       ██████╔╝█████╗  ██║   ██║███████╗   ║
║  ██║     ██║   ██║██║  ██║██╔══╝       ██╔══██╗██╔══╝  ██║   ██║╚════██║   ║
║  ╚██████╗╚██████╔╝██████╔╝███████╗     ██║  ██║███████╗╚██████╔╝███████║   ║
║   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝     ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝   ║
║                                                                              ║
║              Context-Aware Code Generation Agent v1.0                       ║
║              Enforcing Deterministic Code Reuse with AI                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

🚀 Welcome to the Context-Aware Code Generation Demo!

This demo showcases our novel approach to AI code generation:
  ✓ AST-based dependency analysis
  ✓ Vector similarity search for code reuse
  ✓ Dual-phase validation (namespace + structural)
  ✓ Automatic refactoring based on quality scores

```

## 2. Repository Input
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📁 Repository Setup                                                         │
└─────────────────────────────────────────────────────────────────────────────┘

Enter GitHub URL or local repository path:
> https://github.com/user/sample-project

✓ Repository URL validated
✓ Preparing to clone and index...

```

## 3. Live Indexing Dashboard
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔍 Indexing Repository: sample-project                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Phase 1: AST Parsing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:15

Phase 2: Dependency Graph Construction
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:08

Phase 3: Vector Embeddings
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  75% 0:00:12

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 Indexing Statistics                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Files Parsed:           47                                                 │
│  Functions Extracted:    234                                                │
│  Import Statements:      156                                                │
│  Embeddings Created:     234                                                │
│  Dependency Edges:       412                                                │
│                                                                             │
│  Estimated Time:         ~25 seconds                                        │
│  Status:                 ⚡ Processing...                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

[⠋] Creating vector database... (18/234 functions embedded)
```

## 4. Indexing Complete
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ✅ Indexing Complete!                                                       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📈 Repository Analysis Summary                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Total Files:            47                                                 │
│  Total Functions:        234                                                │
│  Total Lines of Code:    8,456                                              │
│                                                                             │
│  Top Modules:                                                               │
│    • utils.py            (45 functions)                                     │
│    • services.py         (38 functions)                                     │
│    • models.py           (32 functions)                                     │
│                                                                             │
│  Dependency Depth:       5 levels                                           │
│  Circular Dependencies:  0 (✓ Clean!)                                       │
│                                                                             │
│  Time Taken:             32.4 seconds                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

✨ Repository is ready for code generation!

```

## 5. Agent Query Interface
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🤖 AI Code Generation Agent                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

What would you like to build?
> Add email validation to the user registration function in user_service.py

✓ Request received
✓ Analyzing target file: src/services/user_service.py
✓ Searching for relevant utilities...

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔎 Context Gathering                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Similar Functions Found: 5                                                 │
│                                                                             │
│  1. validate_email()          [utils/validators.py]      Similarity: 0.92  │
│  2. check_email_format()      [utils/email.py]           Similarity: 0.87  │
│  3. sanitize_input()          [utils/validators.py]      Similarity: 0.78  │
│  4. validate_user_data()      [services/user.py]         Similarity: 0.75  │
│  5. format_email()            [utils/formatters.py]      Similarity: 0.71  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

[⠋] Agent is thinking...
```

## 6. Code Generation with Streaming
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 💻 Generated Code                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

File: src/services/user_service.py

```python
from utils.validators import validate_email
from utils.email import check_email_format

def register_user(username: str, email: str, password: str) -> dict:
    """
    Register a new user with email validation.
    
    Args:
        username: User's username
        email: User's email address
        password: User's password
        
    Returns:
        dict: Registration result with user data
    """
    # Validate email format using existing utility
    if not validate_email(email):
        raise ValueError("Invalid email format")
    
    # Additional email checks
    if not check_email_format(email):
        raise ValueError("Email format check failed")
    
    # Create user record
    user = {
        "username": username,
        "email": email,
        "created_at": datetime.now()
    }
    
    return user
```

✓ Code generation complete!
```

## 7. Score Visualization Dashboard
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 Code Quality Metrics - Iteration #1                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Namespace Reuse Score                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Score: 66.7%  ████████████████████░░░░░░░░░░                              │
│                                                                             │
│  ✓ Functions Called:     3                                                  │
│  ✓ Reused from Repo:     2 (validate_email, check_email_format)            │
│  ✗ New/External:         1 (datetime.now)                                   │
│                                                                             │
│  Status: ⚠️  PASS (Threshold: 40%)                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Structural Similarity Check                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Max Similarity: 23.5%  ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░                │
│                                                                             │
│  ✓ No plagiarism detected                                                   │
│  ✓ Code structure is original                                               │
│                                                                             │
│  Status: ✅ PASS (Threshold: <85%)                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Overall Quality Score                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Score: 78.2%  ███████████████████████░░░░░░░                              │
│                                                                             │
│  ✓ Namespace Reuse:      66.7%                                              │
│  ✓ Structural Check:     PASS                                               │
│  ✓ Dependency Valid:     YES                                                │
│                                                                             │
│  Status: ✅ EXCELLENT - Code meets quality standards!                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

```

## 8. Low Score Example (Triggers Refactor)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 Code Quality Metrics - Iteration #1                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Namespace Reuse Score                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Score: 25.0%  ████████░░░░░░░░░░░░░░░░░░░░░░░░                            │
│                                                                             │
│  ✗ Functions Called:     4                                                  │
│  ✓ Reused from Repo:     1 (validate_email)                                 │
│  ✗ New/External:         3 (re.match, str.lower, len)                      │
│                                                                             │
│  Status: ❌ FAIL (Below 40% threshold)                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

⚠️  Code quality below threshold! Initiating automatic refactor...

┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔄 Refactoring Suggestions                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  The code has low reuse score. Consider using these existing functions:    │
│                                                                             │
│  • check_email_format() - Already handles regex validation                 │
│  • sanitize_input() - Handles string normalization                         │
│  • validate_user_data() - Comprehensive validation logic                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

[⠋] Refactoring code... (Iteration #2)
```

## 9. Refactor Iteration with Improvement
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🔄 Refactored Code - Iteration #2                                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┬──────────────────────────────────────────────┐
│ ❌ Before (Score: 25%)       │ ✅ After (Score: 75%)                        │
├──────────────────────────────┼──────────────────────────────────────────────┤
│                              │                                              │
│ import re                    │ from utils.validators import (              │
│                              │     validate_email,                          │
│ def register_user(...):      │     sanitize_input                           │
│     # Manual regex           │ )                                            │
│     pattern = r'^[\w\.-]+'   │ from utils.email import (                   │
│     if not re.match(...):    │     check_email_format                       │
│         raise ValueError     │ )                                            │
│                              │                                              │
│     email = email.lower()    │ def register_user(...):                     │
│     ...                      │     # Use existing utilities                 │
│                              │     email = sanitize_input(email)            │
│                              │     if not validate_email(email):            │
│                              │         raise ValueError                     │
│                              │     if not check_email_format(email):        │
│                              │         raise ValueError                     │
│                              │     ...                                      │
│                              │                                              │
└──────────────────────────────┴──────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📊 Improved Metrics                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Namespace Reuse:    25% → 75%  ⬆️ +50%                                     │
│  Overall Quality:    42% → 82%  ⬆️ +40%                                     │
│                                                                             │
│  Status: ✅ PASS - Quality threshold met!                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 10. Final Summary
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ✨ Code Generation Complete!                                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 📈 Session Summary                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Total Iterations:           2                                              │
│  Final Namespace Reuse:      75.0%                                          │
│  Final Quality Score:        82.3%                                          │
│                                                                             │
│  Functions Reused:           3                                              │
│    • validate_email()                                                       │
│    • check_email_format()                                                   │
│    • sanitize_input()                                                       │
│                                                                             │
│  Time Taken:                 8.7 seconds                                    │
│  Status:                     ✅ SUCCESS                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 💾 Output                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Generated code saved to: src/services/user_service.py                      │
│  Metrics report saved to: ./reports/generation_metrics.json                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

🎉 Thank you for using Context-Aware Code Generation Agent!

   Key Achievements:
   ✓ Enforced code reuse (75% of functions from existing codebase)
   ✓ Prevented code duplication through structural analysis
   ✓ Validated dependencies automatically
   ✓ Achieved high quality score (82.3%)

   This demonstrates our novel approach to deterministic code reuse!

```

---

## Color Scheme

- **Green (✅)**: Success, high scores, passed checks
- **Red (❌)**: Failures, low scores, errors
- **Yellow (⚠️)**: Warnings, medium scores, attention needed
- **Blue (ℹ️)**: Information, neutral status
- **Cyan**: Headers, titles, emphasis
- **Magenta**: Code, technical details

## Animation Elements

- Progress bars with percentage
- Spinners for loading states
- Live updating counters
- Smooth transitions between screens
- Syntax highlighting for code blocks

---

This mockup shows a professional, visually appealing demo that will look excellent in a hackathon video! 🚀