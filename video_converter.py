"""
Video Converter Module
Converts and fixes video files to meet WhatsApp API specifications
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Callable


class VideoConverter:
    """Converts videos to WhatsApp API compliant format"""

    def __init__(self, input_path: str, output_path: Optional[str] = None):
        """
        Initialize converter

        Args:
            input_path: Path to input video file
            output_path: Path for output file (optional)
        """
        self.input_path = input_path
        self.output_path = output_path or self._generate_output_path()

    def _generate_output_path(self) -> str:
        """Generate output path based on input path"""
        input_file = Path(self.input_path)
        output_file = input_file.parent / f"{input_file.stem}_fixed.mp4"
        return str(output_file)

    def convert(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Convert video to WhatsApp API compliant format

        Args:
            progress_callback: Optional callback function for progress updates

        Returns:
            Dictionary with conversion results
        """
        result = {
            'success': False,
            'output_path': self.output_path,
            'message': '',
            'error': None
        }

        try:
            # Build ffmpeg command for WhatsApp compliance
            cmd = self._build_ffmpeg_command()

            if progress_callback:
                progress_callback("Starting conversion...")

            # Run conversion
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Capture output
            stderr_output = []
            for line in process.stderr:
                stderr_output.append(line)
                if progress_callback and 'time=' in line:
                    progress_callback(f"Converting: {line.strip()}")

            process.wait()

            if process.returncode == 0:
                # Verify output file exists
                if os.path.exists(self.output_path):
                    file_size_mb = os.path.getsize(self.output_path) / (1024 * 1024)

                    if file_size_mb > 16:
                        result['success'] = False
                        result['message'] = f"Output file too large: {file_size_mb:.2f} MB (Max: 16 MB)"
                        result['error'] = 'File size exceeds maximum after conversion'
                    else:
                        result['success'] = True
                        result['message'] = f"Conversion successful! Output: {os.path.basename(self.output_path)}"
                else:
                    result['success'] = False
                    result['message'] = 'Conversion failed: output file not created'
                    result['error'] = 'Output file missing'
            else:
                error_msg = '\n'.join(stderr_output[-20:])  # Last 20 lines
                result['success'] = False
                result['message'] = 'Conversion failed'
                result['error'] = error_msg

        except Exception as e:
            result['success'] = False
            result['message'] = f'Conversion error: {str(e)}'
            result['error'] = str(e)

        return result

    def _build_ffmpeg_command(self) -> list:
        """
        Build ffmpeg command for WhatsApp API compliance

        Returns:
            List of command arguments
        """
        cmd = [
            'ffmpeg',
            '-i', self.input_path,
            '-y',  # Overwrite output file

            # Video codec settings
            '-c:v', 'libx264',  # H.264 codec
            '-profile:v', 'main',  # Main profile (or baseline)
            '-level:v', '3.0',  # Level 3.0
            '-pix_fmt', 'yuv420p',  # Required pixel format

            # Video quality and size optimization
            '-preset', 'slow',  # Better compression
            '-crf', '23',  # Constant Rate Factor (quality)

            # Audio codec settings
            '-c:a', 'aac',  # AAC codec
            '-profile:a', 'aac_low',  # AAC-LC profile
            '-ac', '1',  # Mono audio (reduces size)
            '-ar', '44100',  # Sample rate
            '-b:a', '64k',  # Audio bitrate (low to save space)

            # Container and moov atom
            '-f', 'mp4',  # MP4 container
            '-movflags', '+faststart',  # Move moov atom to beginning

            # Single audio stream
            '-map', '0:v:0',  # First video stream
            '-map', '0:a:0?',  # First audio stream (optional)

            self.output_path
        ]

        return cmd

    def fix_moov_atom(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Fix moov atom position without re-encoding (fast operation)

        Args:
            progress_callback: Optional callback function for progress updates

        Returns:
            Dictionary with fix results
        """
        result = {
            'success': False,
            'output_path': self.output_path,
            'message': '',
            'error': None
        }

        try:
            if progress_callback:
                progress_callback("Moving moov atom to beginning...")

            # Use ffmpeg with -movflags faststart to fix moov atom
            # This is much faster than re-encoding
            cmd = [
                'ffmpeg',
                '-i', self.input_path,
                '-y',
                '-c', 'copy',  # Copy streams without re-encoding
                '-movflags', '+faststart',  # Move moov atom to beginning
                self.output_path
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if process.returncode == 0 and os.path.exists(self.output_path):
                result['success'] = True
                result['message'] = f"moov atom fixed! Output: {os.path.basename(self.output_path)}"
            else:
                result['success'] = False
                result['message'] = 'Failed to fix moov atom'
                result['error'] = process.stderr

        except Exception as e:
            result['success'] = False
            result['message'] = f'Error fixing moov atom: {str(e)}'
            result['error'] = str(e)

        return result

    def optimize_size(self, target_size_mb: float = 15.0, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Optimize video size to fit within target size

        Args:
            target_size_mb: Target file size in MB
            progress_callback: Optional callback function

        Returns:
            Dictionary with optimization results
        """
        result = {
            'success': False,
            'output_path': self.output_path,
            'message': '',
            'error': None
        }

        try:
            if progress_callback:
                progress_callback(f"Optimizing video to fit {target_size_mb} MB...")

            # Get video duration
            duration = self._get_video_duration()

            if not duration:
                result['message'] = 'Could not determine video duration'
                return result

            # Calculate target bitrate
            # Formula: bitrate = (target_size * 8192) / duration - audio_bitrate
            target_size_kbits = target_size_mb * 8192
            audio_bitrate = 64  # kbps
            video_bitrate = int((target_size_kbits / duration) - audio_bitrate)

            if video_bitrate < 100:
                result['message'] = f'Video too long for target size. Minimum bitrate: {video_bitrate} kbps'
                return result

            # Build optimized ffmpeg command
            cmd = [
                'ffmpeg',
                '-i', self.input_path,
                '-y',

                # Video settings
                '-c:v', 'libx264',
                '-profile:v', 'main',
                '-level:v', '3.0',
                '-pix_fmt', 'yuv420p',
                '-b:v', f'{video_bitrate}k',
                '-maxrate', f'{video_bitrate}k',
                '-bufsize', f'{video_bitrate * 2}k',
                '-preset', 'slow',

                # Audio settings
                '-c:a', 'aac',
                '-profile:a', 'aac_low',
                '-ac', '1',
                '-ar', '44100',
                '-b:a', f'{audio_bitrate}k',

                # Container
                '-f', 'mp4',
                '-movflags', '+faststart',

                self.output_path
            ]

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if process.returncode == 0 and os.path.exists(self.output_path):
                output_size_mb = os.path.getsize(self.output_path) / (1024 * 1024)
                result['success'] = True
                result['message'] = f"Optimized to {output_size_mb:.2f} MB"
            else:
                result['success'] = False
                result['message'] = 'Optimization failed'
                result['error'] = process.stderr

        except Exception as e:
            result['success'] = False
            result['message'] = f'Error optimizing: {str(e)}'
            result['error'] = str(e)

        return result

    def _get_video_duration(self) -> Optional[float]:
        """Get video duration in seconds"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                self.input_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return float(result.stdout.strip())

            return None

        except Exception:
            return None
