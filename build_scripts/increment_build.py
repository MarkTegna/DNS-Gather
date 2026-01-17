"""
Increment build version for DNS-Gather
Supports automatic builds (letter suffix) and user builds (no letter)
"""

import re
import sys
from pathlib import Path
from datetime import datetime


def parse_version(version_str):
    """Parse version string into components"""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)([a-z]?)$', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    
    major, minor, patch, letter = match.groups()
    return int(major), int(minor), int(patch), letter


def increment_version(version_str, build_type='auto'):
    """
    Increment version based on build type
    
    Args:
        version_str: Current version (e.g., "0.0.1" or "0.0.1a")
        build_type: 'auto' for automatic build (add/increment letter)
                   'user' for user build (remove letter, increment patch)
    
    Returns:
        New version string
    """
    major, minor, patch, letter = parse_version(version_str)
    
    if build_type == 'auto':
        # Automatic build: add or increment letter
        if not letter:
            letter = 'a'
        elif letter == 'z':
            # Letter overflow: increment patch, reset to 'a'
            patch += 1
            letter = 'a'
        else:
            letter = chr(ord(letter) + 1)
        return f"{major}.{minor}.{patch}{letter}"
    
    elif build_type == 'user':
        # User build: remove letter, increment patch
        patch += 1
        return f"{major}.{minor}.{patch}"
    
    else:
        raise ValueError(f"Invalid build type: {build_type}")


def update_version_file(new_version):
    """Update version.py with new version and compile date"""
    version_file = Path(__file__).parent.parent / 'dns_gather' / 'version.py'
    
    compile_date = datetime.now().strftime("%Y-%m-%d")
    
    content = f'''"""Version information for DNS-Gather"""

from datetime import datetime

__version__ = "{new_version}"
__author__ = "Mark Oldham"
__compile_date__ = "{compile_date}"
'''
    
    version_file.write_text(content, encoding='utf-8')
    print(f"[OK] Updated version to {new_version}")
    print(f"[OK] Updated compile date to {compile_date}")


def main():
    """Main entry point"""
    # Determine build type from command line or default to 'auto'
    build_type = sys.argv[1] if len(sys.argv) > 1 else 'auto'
    
    if build_type not in ['auto', 'user']:
        print(f"[FAIL] Invalid build type: {build_type}")
        print("Usage: python increment_build.py [auto|user]")
        sys.exit(1)
    
    # Read current version
    version_file = Path(__file__).parent.parent / 'dns_gather' / 'version.py'
    
    if not version_file.exists():
        print("[FAIL] version.py not found")
        sys.exit(1)
    
    content = version_file.read_text(encoding='utf-8')
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    
    if not match:
        print("[FAIL] Could not find version in version.py")
        sys.exit(1)
    
    current_version = match.group(1)
    print(f"Current version: {current_version}")
    
    # Increment version
    try:
        new_version = increment_version(current_version, build_type)
        print(f"New version: {new_version} ({build_type} build)")
        
        # Update version file
        update_version_file(new_version)
        
    except ValueError as e:
        print(f"[FAIL] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
