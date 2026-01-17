---
inclusion: always
---

# Lessons Learned - Project-Specific

## PowerShell Execution
When running an executable in PowerShell, you must start the command with `.\`

Example:
```powershell
.\project.exe
```

## Test File Management
Copy the test_files into your working directory instead of pathing to them so that your updates do not carry over to the next test cycle.

## Build Script Automation
Remove "Read-Host 'Press Enter to exit'" prompts from PowerShell build scripts to allow automated builds without user interaction.

## Unicode Logging Errors on Windows
- Windows console uses cp1252 encoding which doesn't support Unicode box-drawing characters (║, ╔, ╚, ╠, ═) or symbols (✓, ✗)
- Replace Unicode characters with ASCII equivalents:
  - ║ → |
  - ╔╚╠ → +
  - ═ → =
  - ✓ → [OK]
  - ✗ → [FAIL]
- This prevents `UnicodeEncodeError: 'charmap' codec can't encode character` errors in logging

## Python Bytecode Cache Issues
- When running Python source code directly (not built executable), cached .pyc files in `__pycache__` directories can cause old code to run
- **Symptoms**: Config files are correct, source code is correct, but behavior shows old code is executing
- **Solution**: Clear all `__pycache__` directories and .pyc files using `clear_python_cache.ps1`
- **Prevention**: Use `python -B` flag during development to prevent bytecode generation, or always run built executables for testing
- **Rule**: If config changes don't take effect, always suspect cached bytecode first

## PyInstaller Build Cache Issues
- **CRITICAL**: PyInstaller can package old cached .pyc files into the executable, causing regression issues
- **Symptoms**: Source code is updated and correct, but built executable shows old behavior
- **Solution**: ALWAYS run `clear_python_cache.ps1` BEFORE running `build_executable.py`
- **Build process**: 
  1. Clear cache
  2. Build executable
  3. Test
- Never skip the cache clearing step when building executables after code changes
- If a built executable doesn't reflect recent code changes, cached bytecode was likely packaged into the build

## Version Management for Builds
- Use **AUTOMATIC builds** (letter suffix) for development/troubleshooting
- Use **USER builds** (no letter) only when user explicitly says "build"
- **Automatic build sequence**: 0.4.13 → 0.4.13a → 0.4.13b → 0.4.13c (for testing/development)
- **User build**: 0.4.13c → 0.4.14 (when user says "build" for final testing)
- **Default behavior**: Use automatic builds unless user explicitly requests "build"

## Excel File Locking on Windows
- **Issue**: openpyxl keeps Excel files open even after wb.close(), causing PermissionError during test teardown
- **Symptoms**: Tests pass but teardown fails with "The process cannot access the file because it is being used by another process"
- **Solution**: Add time.sleep(0.1) after closing workbooks in fixtures, or use tempfile.TemporaryDirectory with ignore_cleanup_errors=True
- **Acceptable**: Teardown errors are acceptable if tests themselves pass - it's just a cleanup issue
