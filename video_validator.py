"""
Video Validator Module
Validates video files against WhatsApp API specifications
"""
import os
import struct
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from logger_config import setup_logger

# Initialize logger
logger = setup_logger("video_validator")


class VideoValidator:
    """Validates video files for WhatsApp API compliance"""

    # Validation criteria
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB
    ALLOWED_VIDEO_CODECS = ['h264']
    ALLOWED_PROFILES = ['Baseline', 'Main', 'Constrained Baseline']
    RECOMMENDED_LEVEL = '3.0'
    MAX_LEVEL = '3.1'
    ALLOWED_AUDIO_CODECS = ['aac']
    ALLOWED_CONTAINERS = ['mp4', 'mov', 'qt', '3gp']
    REQUIRED_PIXEL_FORMAT = 'yuv420p'

    def __init__(self, video_path: str):
        """
        Initialize validator with video path

        Args:
            video_path: Path to the video file
        """
        self.video_path = video_path
        self.file_size = os.path.getsize(video_path) if os.path.exists(video_path) else 0
        self.validation_results = {}
        logger.debug(f"Initialized VideoValidator for: {video_path}")

    def validate_all(self) -> Dict:
        """
        Run all validations and return comprehensive results

        Returns:
            Dictionary with validation results
        """
        results = {
            'file_path': self.video_path,
            'file_size': self.file_size,
            'file_size_mb': round(self.file_size / (1024 * 1024), 2),
            'validations': {},
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'video_info': {}
        }

        # Check if file exists
        if not os.path.exists(self.video_path):
            logger.error(f"File not found: {self.video_path}")
            results['is_valid'] = False
            results['errors'].append('File does not exist')
            return results

        # Get video information
        video_info = self._get_video_info()
        results['video_info'] = video_info

        if video_info.get('error') == 'ffprobe not found':
            results['is_valid'] = False
            results['errors'].append('FFmpeg/FFprobe is not installed. Please install FFmpeg from https://ffmpeg.org/download.html')
            return results

        if not video_info.get('streams'):
            logger.warning(f"No streams found in file: {self.video_path}")
            results['is_valid'] = False
            results['errors'].append('Unable to read video file or invalid format')
            return results

        # Run individual validations
        validations = [
            self._validate_file_size,
            self._validate_container_format,
            self._validate_video_codec,
            self._validate_audio_codec,
            self._validate_audio_streams,
            self._validate_pixel_format,
            self._validate_moov_atom
        ]

        for validation_func in validations:
            validation_name, is_valid, message, details = validation_func(video_info)
            results['validations'][validation_name] = {
                'valid': is_valid,
                'message': message,
                'details': details
            }

            if not is_valid:
                results['is_valid'] = False
                results['errors'].append(f"{validation_name}: {message}")
            elif details.get('warning'):
                results['warnings'].append(f"{validation_name}: {details['warning']}")
        
        logger.info(f"Validation complete. Valid: {results['is_valid']}")
        if not results['is_valid']:
            logger.info(f"Validation errors: {results['errors']}")

        return results

    def _get_video_info(self) -> Dict:
        """
        Get video file information using ffprobe

        Returns:
            Dictionary with video information
        """
        # Check if ffprobe is available
        if not shutil.which('ffprobe'):
            logger.error("FFprobe not found in system PATH")
            return {'streams': [], 'format': {}, 'error': 'ffprobe not found'}

        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                self.video_path
            ]
            
            # logger.debug(f"Running ffprobe: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"FFprobe failed with return code {result.returncode}")
                return {'streams': [], 'format': {}}

        except Exception as e:
            logger.exception("Error getting video info")
            return {'streams': [], 'format': {}}

    def _validate_file_size(self, video_info: Dict) -> Tuple[str, bool, str, Dict]:
        """Validate file size"""
        is_valid = self.file_size <= self.MAX_FILE_SIZE

        return (
            'File Size',
            is_valid,
            f"File size: {round(self.file_size / (1024 * 1024), 2)} MB (Max: 16 MB)" if is_valid
            else f"File too large: {round(self.file_size / (1024 * 1024), 2)} MB (Max: 16 MB)",
            {
                'size_bytes': self.file_size,
                'size_mb': round(self.file_size / (1024 * 1024), 2),
                'max_mb': 16
            }
        )

    def _validate_container_format(self, video_info: Dict) -> Tuple[str, bool, str, Dict]:
        """Validate container format (MP4, 3GP)"""
        format_name = video_info.get('format', {}).get('format_name', '').lower()
        format_parts = format_name.split(',')

        is_valid = any(fmt in self.ALLOWED_CONTAINERS for fmt in format_parts)

        return (
            'Container Format',
            is_valid,
            f"Format: {format_name} ✓" if is_valid
            else f"Invalid format: {format_name} (Expected: MP4 or 3GP)",
            {
                'format': format_name,
                'allowed_formats': self.ALLOWED_CONTAINERS
            }
        )

    def _validate_video_codec(self, video_info: Dict) -> Tuple[str, bool, str, Dict]:
        """Validate video codec (H.264/AVC, Baseline or Main profile, Level 3.0-3.1)"""
        video_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'video']

        if not video_streams:
            return ('Video Codec', False, 'No video stream found', {})

        video_stream = video_streams[0]
        codec = video_stream.get('codec_name', '').lower()
        profile = video_stream.get('profile', '')
        level = video_stream.get('level', 0)

        # Convert level to readable format (e.g., 30 -> 3.0)
        level_str = f"{level / 10:.1f}" if level > 0 else 'Unknown'

        errors = []
        warnings = []

        # Check codec
        if codec not in self.ALLOWED_VIDEO_CODECS:
            errors.append(f"Invalid codec: {codec}")

        # Check profile
        if profile not in self.ALLOWED_PROFILES:
            errors.append(f"Invalid profile: {profile}")

        # Check level
        level_float = level / 10 if level > 0 else 0
        if level_float > 3.1:
            errors.append(f"Level too high: {level_str}")
        elif level_float != 3.0:
            warnings.append(f"Level {level_str} (Recommended: 3.0)")

        is_valid = len(errors) == 0

        message_parts = []
        if codec in self.ALLOWED_VIDEO_CODECS:
            message_parts.append(f"Codec: {codec.upper()}")
        if profile:
            message_parts.append(f"Profile: {profile}")
        if level_str != 'Unknown':
            message_parts.append(f"Level: {level_str}")

        message = ', '.join(message_parts) if is_valid else '; '.join(errors)

        return (
            'Video Codec',
            is_valid,
            message,
            {
                'codec': codec,
                'profile': profile,
                'level': level_str,
                'warning': warnings[0] if warnings else None
            }
        )

    def _validate_audio_codec(self, video_info: Dict) -> Tuple[str, bool, str, Dict]:
        """Validate audio codec (AAC-LC)"""
        audio_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'audio']

        if not audio_streams:
            # No audio is acceptable
            return ('Audio Codec', True, 'No audio stream (acceptable)', {'has_audio': False})

        audio_stream = audio_streams[0]
        codec = audio_stream.get('codec_name', '').lower()
        profile = audio_stream.get('profile', '').lower()

        is_valid = codec in self.ALLOWED_AUDIO_CODECS

        # Check if it's AAC-LC specifically
        if is_valid and profile and 'lc' not in profile.lower():
            return (
                'Audio Codec',
                False,
                f"Audio must be AAC-LC (found: {profile})",
                {'codec': codec, 'profile': profile}
            )

        return (
            'Audio Codec',
            is_valid,
            f"Codec: AAC-LC ✓" if is_valid else f"Invalid audio codec: {codec}",
            {'codec': codec, 'profile': profile}
        )

    def _validate_audio_streams(self, video_info: Dict) -> Tuple[str, bool, str, Dict]:
        """Validate number of audio streams (0 or 1)"""
        audio_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'audio']
        count = len(audio_streams)

        is_valid = count <= 1

        return (
            'Audio Streams',
            is_valid,
            f"Audio streams: {count} ✓" if is_valid else f"Too many audio streams: {count} (Max: 1)",
            {'count': count}
        )

    def _validate_pixel_format(self, video_info: Dict) -> Tuple[str, bool, str, Dict]:
        """Validate pixel format (yuv420p)"""
        video_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'video']

        if not video_streams:
            return ('Pixel Format', False, 'No video stream found', {})

        video_stream = video_streams[0]
        pix_fmt = video_stream.get('pix_fmt', '')

        is_valid = pix_fmt == self.REQUIRED_PIXEL_FORMAT

        return (
            'Pixel Format',
            is_valid,
            f"Format: {pix_fmt} ✓" if is_valid else f"Invalid pixel format: {pix_fmt} (Required: {self.REQUIRED_PIXEL_FORMAT})",
            {'format': pix_fmt}
        )

    def _validate_moov_atom(self, video_info: Dict) -> Tuple[str, bool, str, Dict]:
        """
        Validate moov atom location (must be at the beginning for progressive download)
        """
        try:
            moov_position = self._find_moov_atom()

            if moov_position is None:
                return (
                    'Progressive Download (moov atom)',
                    False,
                    'moov atom not found in file',
                    {'moov_found': False}
                )

            # moov atom should be within the first few KB for fast start
            # Typically after ftyp atom (which is usually < 32 bytes)
            is_optimized = moov_position < 10000  # Within first ~10KB

            return (
                'Progressive Download (moov atom)',
                is_optimized,
                f"moov atom at position {moov_position} bytes ✓" if is_optimized
                else f"moov atom at position {moov_position} bytes (should be at beginning)",
                {
                    'moov_position': moov_position,
                    'is_optimized': is_optimized
                }
            )

        except Exception as e:
            logger.exception("Error in _validate_moov_atom")
            return (
                'Progressive Download (moov atom)',
                False,
                f'Error checking moov atom: {str(e)}',
                {'error': str(e)}
            )

    def _find_moov_atom(self) -> Optional[int]:
        """
        Find the position of the moov atom in the MP4 file

        Returns:
            Position of moov atom in bytes, or None if not found
        """
        try:
            with open(self.video_path, 'rb') as f:
                # Read file in chunks to find moov atom
                position = 0

                while True:
                    # Read atom header (8 bytes: 4 for size, 4 for type)
                    header = f.read(8)
                    if len(header) < 8:
                        break

                    # Parse atom size and type
                    atom_size = struct.unpack('>I', header[0:4])[0]
                    atom_type = header[4:8].decode('ascii', errors='ignore')

                    # Check if this is the moov atom
                    if atom_type == 'moov':
                        return position

                    # Handle special cases
                    if atom_size == 0:
                        # Atom extends to end of file
                        break
                    elif atom_size == 1:
                        # 64-bit size follows
                        extended_size = f.read(8)
                        if len(extended_size) < 8:
                            break
                        atom_size = struct.unpack('>Q', extended_size)[0]
                        position += 8

                    # Move to next atom
                    position += atom_size
                    f.seek(position)

                return None

        except Exception as e:
            logger.exception("Error finding moov atom")
            return None


def format_validation_report(results: Dict) -> str:
    """
    Format validation results as a readable report

    Args:
        results: Validation results dictionary

    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 60)
    report.append("VIDEO VALIDATION REPORT")
    report.append("=" * 60)
    report.append(f"File: {os.path.basename(results['file_path'])}")
    report.append(f"Size: {results['file_size_mb']} MB")
    report.append("")

    if results['is_valid']:
        report.append("✓ VIDEO IS VALID FOR WHATSAPP API")
    else:
        report.append("✗ VIDEO DOES NOT MEET REQUIREMENTS")

    report.append("")
    report.append("VALIDATION DETAILS:")
    report.append("-" * 60)

    for name, validation in results['validations'].items():
        status = "✓" if validation['valid'] else "✗"
        report.append(f"{status} {name}: {validation['message']}")

    if results['warnings']:
        report.append("")
        report.append("WARNINGS:")
        report.append("-" * 60)
        for warning in results['warnings']:
            report.append(f"⚠ {warning}")

    if results['errors']:
        report.append("")
        report.append("ERRORS:")
        report.append("-" * 60)
        for error in results['errors']:
            report.append(f"✗ {error}")

    report.append("=" * 60)

    return "\n".join(report)
