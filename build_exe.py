import PyInstaller.__main__
import os
import shutil
import sys

# Ensure we are in the script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Clean up previous builds
if os.path.exists('dist'):
    try:
        shutil.rmtree('dist')
    except Exception as e:
        print(f"Warning: Could not clean dist folder: {e}")

if os.path.exists('build'):
    try:
        shutil.rmtree('build')
    except Exception as e:
        print(f"Warning: Could not clean build folder: {e}")

# Separator for add-data depends on OS
sep = ';' if os.name == 'nt' else ':'

print("Building recognition_worker...")
PyInstaller.__main__.run([
    'recognition_worker.py',
    '--onefile',
    '--name=recognition_worker',
    f'--add-data=ncm-afp{sep}ncm-afp',
    '--hidden-import=pythonmonkey',
    '--hidden-import=pyncm',
    '--clean',
    '--log-level=WARN'
])

print("Building MKVChapterGUI...")
PyInstaller.__main__.run([
    'mkv_chapter_gui.py',
    '--onefile',
    '--name=MKVChapterGUI',
    '--windowed',
    f'--add-data=ncm-afp{sep}ncm-afp',
    '--hidden-import=pythonmonkey',
    '--hidden-import=pyncm',
    '--clean',
    '--log-level=WARN'
])

print("Build complete. Files are in 'dist' folder.")
