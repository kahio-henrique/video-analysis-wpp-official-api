"""
Video Converter Module
Converts and fixes video files to meet WhatsApp API specifications
"""
import os
import subprocess
import shutil
import re
from pathlib import Path
from typing import Dict, Optional, Callable
from logger_config import setup_logger

# Initialize logger
logger = setup_logger("video_converter")


def check_ffmpeg_installed() -> tuple[bool, str]:
    """
    Check if FFmpeg is installed and accessible

    Returns:
        Tuple of (is_installed: bool, message: str)
    """
    ffmpeg_path = shutil.which('ffmpeg')
    ffprobe_path = shutil.which('ffprobe')

    if not ffmpeg_path:
        logger.error("FFmpeg not found in system PATH")
        return False, "FFmpeg is not installed or not in system PATH. Please install FFmpeg from https://ffmpeg.org/download.html"

    if not ffprobe_path:
        logger.error("FFprobe not found in system PATH")
        return False, "FFprobe is not installed or not in system PATH. Please install FFmpeg (includes ffprobe) from https://ffmpeg.org/download.html"

    logger.debug(f"FFmpeg found at: {ffmpeg_path}")
    return True, f"FFmpeg found at: {ffmpeg_path}"


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
        logger.debug(f"Initialized VideoConverter: input={input_path}, output={self.output_path}")

    def _generate_output_path(self) -> str:
        """Generate output path based on input path"""
        input_file = Path(self.input_path)
        output_file = input_file.parent / f"{input_file.stem}_fixed.mp4"
        return str(output_file)

    def convert(self, max_size_mb: float = 16.0, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Convert video to WhatsApp API compliant format

        Args:
            max_size_mb: Maximum allowed file size in MB (default: 16.0)
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

        # Check if FFmpeg is installed
        is_installed, message = check_ffmpeg_installed()
        if not is_installed:
            result['message'] = message
            result['error'] = 'FFmpeg not found'
            return result

        try:
            # Get video duration for progress calculation
            duration = self._get_video_duration()
            
            # Check file size and determine encoding strategy
            input_size_mb = os.path.getsize(self.input_path) / (1024 * 1024)
            target_bitrate = None
            
            # If file is larger than target limit (minus some margin), force bitrate control
            # Use a slightly lower target for calculation to be safe (e.g. 95% of max)
            safe_target_mb = max_size_mb * 0.95
            
            if input_size_mb > (max_size_mb * 0.8):  # If file is approaching the limit
                logger.info(f"Input file size {input_size_mb:.2f}MB. Calculating target bitrate for limit {max_size_mb}MB.")
                if duration:
                    # Formula: bitrate = (target_size * 8192) / duration - audio_bitrate
                    target_size_kbits = safe_target_mb * 8192
                    audio_bitrate = 64  # kbps
                    video_bitrate = int((target_size_kbits / duration) - audio_bitrate)
                    
                    # Ensure minimum bitrate
                    if video_bitrate < 50:
                        logger.warning("Calculated bitrate too low, defaulting to 500k")
                        video_bitrate = 500
                    
                    target_bitrate = video_bitrate
                    logger.info(f"Target bitrate set to {target_bitrate}k for {duration}s video")
                else:
                    logger.warning("Could not determine duration, using default CRF")

            # Build ffmpeg command for WhatsApp compliance
            cmd = self._build_ffmpeg_command(bitrate=target_bitrate)
            logger.info(f"Starting conversion with command: {' '.join(cmd)}")

            if progress_callback:
                progress_callback("Starting conversion...")

            # Run conversion
            # Use DEVNULL for stdout to avoid potential deadlocks since we only care about stderr for stats
            # Add explicit encoding handling to prevent UnicodeDecodeError on Windows
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )

            # Capture output
            stderr_output = []
            line_count = 0
            for line in process.stderr:
                stderr_output.append(line)
                line_count += 1
                
                clean_line = line.strip()
                
                # Progress calculation
                if duration and progress_callback:
                    # Regex to extract time=HH:MM:SS.mm
                    time_match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", clean_line)
                    if time_match:
                        hours, minutes, seconds = map(float, time_match.groups())
                        current_seconds = hours * 3600 + minutes * 60 + seconds
                        percentage = min(int((current_seconds / duration) * 100), 99)
                        progress_callback(f"{percentage}%")
                elif progress_callback and 'time=' in clean_line:
                    # Fallback if duration unknown
                    progress_callback(f"Converting: {clean_line}")
                
                # Log progress every 20 lines or if it contains time/progress info
                if 'time=' in clean_line or line_count % 20 == 0:
                    logger.debug(f"FFmpeg progress: {clean_line}")

            process.wait()
            logger.info(f"FFmpeg process finished with return code: {process.returncode}")

            if process.returncode == 0:
                # Verify output file exists
                if os.path.exists(self.output_path):
                    file_size_mb = os.path.getsize(self.output_path) / (1024 * 1024)
                    logger.info(f"Conversion successful. Output size: {file_size_mb:.2f} MB")

                    if file_size_mb > max_size_mb:
                        logger.warning(f"Converted file too large: {file_size_mb:.2f} MB")
                        result['success'] = False
                        result['message'] = f"Output file too large: {file_size_mb:.2f} MB (Max: {max_size_mb} MB)"
                        result['error'] = 'File size exceeds maximum after conversion'
                    else:
                        result['success'] = True
                        result['message'] = f"Conversion successful! Output: {os.path.basename(self.output_path)}"
                else:
                    logger.error("Output file missing after successful FFmpeg exit")
                    result['success'] = False
                    result['message'] = 'Conversion failed: output file not created'
                    result['error'] = 'Output file missing'
            else:
                error_msg = '\n'.join(stderr_output[-20:])  # Last 20 lines
                full_log = '\n'.join(stderr_output)
                logger.error(f"FFmpeg failed. Last 20 lines of stderr:\n{error_msg}")
                logger.debug(f"Full FFmpeg stderr:\n{full_log}")
                
                result['success'] = False
                result['message'] = 'Conversion failed'
                result['error'] = error_msg

        except Exception as e:
            logger.exception("Exception during conversion")
            result['success'] = False
            result['message'] = f'Conversion error: {str(e)}'
            result['error'] = str(e)

        return result

    def _build_ffmpeg_command(self, bitrate: Optional[int] = None) -> list:
        """
        Build ffmpeg command for WhatsApp API compliance

        Args:
            bitrate: Optional video bitrate in kbps. If provided, overrides CRF.

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
            '-preset', 'fast',  # Faster compression
        ]
        
        if bitrate:
            # Use strict bitrate control
            cmd.extend([
                '-b:v', f'{bitrate}k',
                '-maxrate', f'{bitrate}k',
                '-bufsize', f'{bitrate * 2}k',
            ])
        else:
            # Use Constant Rate Factor (quality based)
            cmd.extend([
                '-crf', '23',
            ])

        # Remaining common settings
        cmd.extend([
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
        ])

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

        # Check if FFmpeg is installed
        is_installed, message = check_ffmpeg_installed()
        if not is_installed:
            result['message'] = message
            result['error'] = 'FFmpeg not found'
            return result

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
            
            logger.info(f"Starting moov atom fix with command: {' '.join(cmd)}")

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if process.returncode == 0 and os.path.exists(self.output_path):
                logger.info("moov atom fix successful")
                result['success'] = True
                result['message'] = f"moov atom fixed! Output: {os.path.basename(self.output_path)}"
            else:
                logger.error(f"moov atom fix failed. Stderr: {process.stderr}")
                result['success'] = False
                result['message'] = 'Failed to fix moov atom'
                result['error'] = process.stderr

        except Exception as e:
            logger.exception("Exception during moov atom fix")
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

        # Check if FFmpeg is installed
        is_installed, message = check_ffmpeg_installed()
        if not is_installed:
            result['message'] = message
            result['error'] = 'FFmpeg not found'
            return result

        try:
            if progress_callback:
                progress_callback(f"Optimizing video to fit {target_size_mb} MB...")

            # Get video duration
            duration = self._get_video_duration()

            if not duration:
                logger.error("Could not determine video duration for optimization")
                result['message'] = 'Could not determine video duration'
                return result

            # Calculate target bitrate
            # Formula: bitrate = (target_size * 8192) / duration - audio_bitrate
            target_size_kbits = target_size_mb * 8192
            audio_bitrate = 64  # kbps
            video_bitrate = int((target_size_kbits / duration) - audio_bitrate)

            if video_bitrate < 100:
                logger.warning(f"Calculated video bitrate {video_bitrate} kbps is too low")
                result['message'] = f'Video too long for target size. Minimum bitrate: {video_bitrate} kbps'
                return result
            
            logger.info(f"Optimizing size. Target: {target_size_mb}MB. Duration: {duration}s. Bitrate: {video_bitrate}k")

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
            
            logger.info(f"Running optimization command: {' '.join(cmd)}")

            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            if process.returncode == 0 and os.path.exists(self.output_path):
                output_size_mb = os.path.getsize(self.output_path) / (1024 * 1024)
                logger.info(f"Optimization successful. Final size: {output_size_mb:.2f} MB")
                result['success'] = True
                result['message'] = f"Optimized to {output_size_mb:.2f} MB"
            else:
                logger.error(f"Optimization failed. Stderr: {process.stderr}")
                result['success'] = False
                result['message'] = 'Optimization failed'
                result['error'] = process.stderr

        except Exception as e:
            logger.exception("Exception during optimization")
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
            
            logger.warning(f"Could not get duration. Stderr: {result.stderr}")
            return None

        except Exception as e:
            logger.exception("Error getting video duration")
            return None
