#!/usr/bin/env python3
"""
Command Line Interface for Video Validator
Usage: python cli.py <video_file> [--convert] [--quick-fix]
"""
import sys
import argparse
from pathlib import Path

from video_validator import VideoValidator, format_validation_report
from video_converter import VideoConverter


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Validate and convert videos for WhatsApp API compliance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py video.mp4                    # Validate only
  python cli.py video.mp4 --convert          # Validate and convert
  python cli.py video.mp4 --quick-fix        # Quick fix moov atom only
  python cli.py video.mp4 -o output.mp4      # Specify output file
        """
    )

    parser.add_argument('video', help='Path to video file')
    parser.add_argument('-c', '--convert', action='store_true',
                        help='Convert video to WhatsApp-compliant format')
    parser.add_argument('-q', '--quick-fix', action='store_true',
                        help='Quick fix moov atom position only (no re-encoding)')
    parser.add_argument('-o', '--output', help='Output file path (default: <input>_fixed.mp4)')

    args = parser.parse_args()

    # Check if file exists
    if not Path(args.video).exists():
        print(f"Error: File not found: {args.video}")
        sys.exit(1)

    print("\n" + "="*60)
    print("VIDEO VALIDATOR - WhatsApp API")
    print("="*60 + "\n")

    # Validate video
    print("Validating video...")
    validator = VideoValidator(args.video)
    results = validator.validate_all()

    # Print validation report
    print(format_validation_report(results))

    # Convert or fix if requested
    if args.convert or args.quick_fix:
        print("\n" + "="*60)

        output_path = args.output
        if not output_path:
            input_file = Path(args.video)
            output_path = str(input_file.parent / f"{input_file.stem}_fixed.mp4")

        converter = VideoConverter(args.video, output_path)

        if args.quick_fix:
            print("QUICK FIX - Repositioning moov atom...")
            print("="*60 + "\n")
            result = converter.fix_moov_atom()
        else:
            print("CONVERTING VIDEO")
            print("="*60 + "\n")
            print("This may take a few minutes depending on video size...")

            def progress_callback(msg):
                print(f"  {msg}")

            result = converter.convert(progress_callback)

        # Print conversion result
        print("\n" + "="*60)
        if result['success']:
            print("SUCCESS!")
            print("="*60)
            print(f"\nOutput file: {result['output_path']}")

            # Validate converted file
            print("\nValidating converted file...")
            validator = VideoValidator(result['output_path'])
            converted_results = validator.validate_all()

            if converted_results['is_valid']:
                print("\n✓ Converted video is WhatsApp API compliant!")
            else:
                print("\n⚠ Warning: Converted video may not be fully compliant")
                print("\nRemaining issues:")
                for error in converted_results['errors']:
                    print(f"  - {error}")
        else:
            print("CONVERSION FAILED")
            print("="*60)
            print(f"\nError: {result['message']}")
            if result.get('error'):
                print(f"\nDetails:\n{result['error']}")
            sys.exit(1)

    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()
