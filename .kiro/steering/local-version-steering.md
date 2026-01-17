---
inclusion: always
---

# Version Management Standards

## Version Number Format
- Use 3 dotted digit version numbers with optional letter suffix: `MAJOR.MINOR.PATCH[LETTER]`
- Examples: `1.2.15`, `0.0.1a`, `0.0.1b`

## Version Increment Rules
- Initial version number should be 0.0.1

### Build Type Versioning
- **Automatic builds** (troubleshooting, implementing changes): Add/increment letter after PATCH
- **User-requested builds** (when user says "build"): Remove letter and increment PATCH

### Version Progression Examples
```
0.0.1 → 0.0.1a (automatic build)
0.0.1a → 0.0.1b (automatic build)
0.0.1b → 0.0.2 (user-requested build)
0.0.2 → 0.0.2a (automatic build)
```

### MAJOR Version (First Digit)
- Increment when making incompatible API changes
- Increment when adding major new features that change the core functionality
- **When incremented**: update dist directory and create zip distribution file update GitHub when Major version is incremented.
- **Reset**: MINOR and PATCH to 0, remove any letter suffix

### MINOR Version (Second Digit)  
- Increment when adding functionality in a backwards compatible manner
- Increment when adding new features or significant enhancements
- **When incremented**: update dist directory and create zip distribution file
- **When feature is complete, increment MINOR version, build, push to GitHub
- **Reset**: PATCH to 0, remove any letter suffix

### PATCH Version (Third Digit)
- **CRITICAL**: Only increment when user explicitly requests a build
- Increment for backwards compatible bug fixes
- Increment for small improvements and patches
- **When incremented**: Remove any letter suffix and update dist directory and create zip distribution file
- No GitHub update required (unless told to update GitHub)

### Letter Suffix (Fourth Component)
- **CRITICAL**: Increment letter for EVERY automatic build (a, b, c, d, etc.)
- Used for troubleshooting builds and implementation changes
- Removed when user requests an official build
- **When incremented**: No distribution files created (development only)
- **Letter overflow**: If letter reaches 'z', increment PATCH version and reset letter to 'a'

## Build Process Requirements

### Automatic Version Increment
1. **For automatic builds**: Increment letter suffix (a, b, c, etc.)
2. **For user-requested builds**: Remove letter suffix and increment PATCH version
3. **After successful build**: Version file should reflect new version number
4. **Build artifacts**: Only created for user-requested builds (no letter suffix)

### Manual Version Updates
- MAJOR/MINOR versions should be updated manually when appropriate
- Use version management scripts to update version numbers
- Always commit version changes to source control

## Implementation Requirements

### Version File Structure
```python
# In project/version.py
__version__ = "1.0.15"    # User build (no letter)
__version__ = "1.0.15a"   # Automatic build (with letter)
__author__ = "Mark Oldham"
__compile_date__ = "2026-01-01"
```

### Build Scripts
- `increment_build.py`: Must increment letter for automatic builds, PATCH for user builds
- `update_version.py`: For manual MAJOR/MINOR version updates
- Version increment must be atomic and fail-safe
- Must detect build type (automatic vs user-requested)

### Distribution Requirements
- **User builds only**: Create executable and ZIP distribution
- Executable filename must not include version: `project.exe`
- ZIP distribution must include version: `project_v1.0.15.zip` (no letter suffix)
- Automatic builds (with letters) do NOT create distribution files
- **Archive requirement**: Copy every ZIP file to `/Archive` directory (create if it doesn't exist)

## GitHub Integration

### Repository Updates
- Push to GitHub only when told to.
- Tag releases with version numbers: `v1.0.15`
- Include version information in release notes
- Include pushing zip file to releases when updating GitHub
- Every time a zip file is created, copy it to "\Archive", create the directory if it does not exist
- Before pushing to github, verify that this version hasn't already been pushed

### Version History
- Maintain CHANGELOG.md with version history
- Document what changed in each version
- Link versions to GitHub releases

## Enforcement

### Build Validation
- Build process MUST fail if version increment fails
- Version number MUST be validated before creating distributions
- No duplicate version numbers allowed

### Quality Gates
- Version increment is mandatory for all builds
- Version format must be validated (3 dotted digits)
- Build artifacts must include correct version information

## Examples

### Automatic Build Sequence (Development)
```
Start:        0.0.1
Auto build:   0.0.1a
Auto build:   0.0.1b
Auto build:   0.0.1c
...
Auto build:   0.0.1z
Auto build:   0.0.2a  (letter overflow: PATCH incremented, letter reset)
User build:   0.0.3   (letter removed, PATCH incremented)
Auto build:   0.0.3a
User build:   0.0.4   (letter removed, PATCH incremented)
```

### Feature Addition
```
Before: 0.0.15c (automatic build)
After:  0.1.0   (MINOR increment, PATCH reset, letter removed)
```

### Major Release
```
Before: 1.5.23b (automatic build)
After:  2.0.0   (MAJOR increment, MINOR/PATCH reset, letter removed)
```

## Error Handling

### Build Failures
- If build fails, do NOT increment version
- Version should only increment on successful completion
- Failed builds should not affect version numbering

### Version Conflicts
- Detect and prevent duplicate version numbers
- Validate version format before increment
- Provide clear error messages for version issues

## Project Information
- Project Name: Defaults (current directory name)
- Current Version: 0.0.1
- Author: Mark Oldham
- Platform: Windows

## Build Configuration
- Target Platform: Windows (.exe)
- Python Version: Latest stable
- Build Tool: PyInstaller or similar
- Output Directory: `dist/`

## Development Workflow
- All configuration in `.ini` files
- Log files use `YYYYMMDD-HH-MM` format
- Docker containers use Ubuntu 24.04 base
- GitHub repository: https://github.com/MarkTegna

## Documentation Standards
- Include author name: "Mark Oldham"
- Include version number and compile date
- Maintain README.md with current version info
- Update CHANGELOG.md for each release

This document ensures consistent version management across all projects and eliminates confusion about when and how to increment version numbers.