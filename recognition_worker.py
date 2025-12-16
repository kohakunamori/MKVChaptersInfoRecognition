import sys
import os
import json
import argparse
import contextlib

# Redirect stdout to stderr to prevent pollution of JSON output
# We keep stderr for logs
sys.stdout = sys.stderr

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from auto_rename_mkv_chapters import AFPInstance, AudioRecognizer
except ImportError:
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mkv', required=True)
    parser.add_argument('--start', type=float, required=True)
    parser.add_argument('--duration', type=int, default=3)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    args = parser.parse_args()

    result = {"success": False, "error": "Unknown error"}

    try:
        # Initialize
        # Note: AFPInstance uses pythonmonkey which might print things or use stderr
        afp = AFPInstance()
        recognizer = AudioRecognizer(afp, ffmpeg_path=args.ffmpeg)
        
        # Extract
        # This might print to stdout/stderr
        samples = recognizer.extract_audio_sample(args.mkv, args.start, args.duration)
        
        if samples:
            # Recognize
            info = recognizer.recognize_song(samples)
            if info:
                result = {"success": True, "data": info}
            else:
                result = {"success": False, "error": "No match found"}
        else:
            result = {"success": False, "error": "Failed to extract audio samples"}
            
    except Exception as e:
        result = {"success": False, "error": str(e)}
        import traceback
        traceback.print_exc()

    # Print JSON result to the REAL stdout
    sys.stdout = sys.__stdout__
    try:
        # Force stdout to use utf-8 encoding to handle special characters on Windows
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
        
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
