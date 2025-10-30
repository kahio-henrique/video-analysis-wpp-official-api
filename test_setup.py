#!/usr/bin/env python3
"""
Test script to verify setup and dependencies
"""
import sys
import subprocess


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✓ Python version OK")
        return True


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            # Extract version from first line
            version_line = result.stdout.split('\n')[0]
            print(f"FFmpeg: {version_line}")
            print("✓ FFmpeg installed")
            return True
        else:
            print("❌ FFmpeg not working properly")
            return False

    except FileNotFoundError:
        print("❌ FFmpeg not found")
        print("\nPlease install FFmpeg:")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"❌ Error checking FFmpeg: {e}")
        return False


def check_ffprobe():
    """Check if FFprobe is installed"""
    try:
        result = subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print("✓ FFprobe installed")
            return True
        else:
            print("❌ FFprobe not working properly")
            return False

    except FileNotFoundError:
        print("❌ FFprobe not found (usually comes with FFmpeg)")
        return False
    except Exception as e:
        print(f"❌ Error checking FFprobe: {e}")
        return False


def check_dependencies():
    """Check Python dependencies"""
    dependencies = [
        'dash',
        'dash_bootstrap_components',
        'ffmpeg',
        'plotly',
    ]

    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep}")
        except ImportError:
            print(f"❌ {dep} not installed")
            all_ok = False

    if not all_ok:
        print("\nInstall missing dependencies:")
        print("  pip install -r requirements.txt")

    return all_ok


def check_modules():
    """Check if our modules can be imported"""
    try:
        from video_validator import VideoValidator
        print("✓ video_validator module")
    except ImportError as e:
        print(f"❌ video_validator module: {e}")
        return False

    try:
        from video_converter import VideoConverter
        print("✓ video_converter module")
    except ImportError as e:
        print(f"❌ video_converter module: {e}")
        return False

    return True


def main():
    """Run all checks"""
    print("="*60)
    print("VIDEO VALIDATOR - Setup Check")
    print("="*60 + "\n")

    checks = [
        ("Python Version", check_python_version),
        ("FFmpeg", check_ffmpeg),
        ("FFprobe", check_ffprobe),
        ("Python Dependencies", check_dependencies),
        ("Project Modules", check_modules),
    ]

    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        print("-" * 60)
        results.append(check_func())

    print("\n" + "="*60)
    if all(results):
        print("✓ ALL CHECKS PASSED")
        print("="*60)
        print("\nYou can now run the application:")
        print("  python app.py")
        print("\nOr use the CLI:")
        print("  python cli.py <video_file>")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("="*60)
        print("\nPlease fix the issues above before running the application.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
