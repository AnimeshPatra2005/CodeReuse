# NumPy Compatibility Fix

## Issue
ChromaDB 0.4.22 is not compatible with NumPy 2.0+, causing this error:
```
AttributeError: `np.float_` was removed in the NumPy 2.0 release
```

## Quick Fix

Run this command to downgrade NumPy:

```bash
pip install "numpy<2.0.0"
```

Or reinstall all dependencies with the updated requirements.txt:

```bash
pip install -r requirements.txt --force-reinstall
```

## Then Run Demo

### PowerShell (Windows) - Single Line:
```powershell
python demo.py --repo https://github.com/AnimeshPatra2005/demo-ecommerce --query "Add email validation to user registration" --target-file services/user_service.py
```

### Or Test Locally First:
```powershell
python demo.py --repo ./demo_repository --query "Add email validation to user registration" --target-file services/user_service.py
```

## Note on PowerShell Multi-line Commands

PowerShell doesn't support `\` for line continuation like bash. Use backtick `` ` `` instead:

```powershell
python demo.py `
  --repo https://github.com/AnimeshPatra2005/demo-ecommerce `
  --query "Add email validation to user registration" `
  --target-file services/user_service.py
```

Or just use a single line (easier).

## Verification

After fixing NumPy, you should see:
1. ✅ Welcome screen with ASCII art
2. ✅ Repository cloning/loading message
3. ✅ Indexing progress bars
4. ✅ Statistics panel
5. ✅ Generated code
6. ✅ Score dashboard
7. ✅ Final summary

---

**Updated requirements.txt already includes the NumPy fix!**