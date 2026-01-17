"""Build DNS-Gather executable using PyInstaller"""

import PyInstaller.__main__
import shutil
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent

# Build configuration
PyInstaller.__main__.run([
    str(project_root / 'dns_gather' / 'main.py'),
    '--name=DNS-Gather',
    '--onefile',
    '--console',
    f'--distpath={project_root / "dist"}',
    f'--workpath={project_root / "build"}',
    f'--specpath={project_root / "build"}',
    '--clean',
    '--noconfirm',
])

# Copy config file to dist
config_src = project_root / 'DNS-Gather.ini'
config_dst = project_root / 'dist' / 'DNS-Gather.ini'

if config_src.exists():
    shutil.copy2(config_src, config_dst)
    print(f"\n[OK] Copied {config_src} to {config_dst}")

print("\n[OK] Build complete!")
print(f"[OK] Executable: {project_root / 'dist' / 'DNS-Gather.exe'}")
