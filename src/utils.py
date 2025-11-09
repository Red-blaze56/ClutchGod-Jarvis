"""
Utility functions for file handling and processing
"""
import os
import subprocess
from pathlib import Path
from datetime import datetime
import streamlit as st
from config import TEMP_DIR, SUPPORTED_VIDEO_FORMATS, SUPPORTED_AUDIO_FORMATS

def get_file_extension(filename: str) -> str:
    """Get lowercase file extension"""
    return Path(filename).suffix.lower()

def is_video_file(filename: str) -> bool:
    """Check if file is a video"""
    return get_file_extension(filename) in SUPPORTED_VIDEO_FORMATS

def is_audio_file(filename: str) -> bool:
    """Check if file is audio"""
    return get_file_extension(filename) in SUPPORTED_AUDIO_FORMATS

def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """Generate unique filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = Path(original_filename).stem
    ext = Path(original_filename).suffix
    return f"{prefix}{name}_{timestamp}{ext}"

def save_uploaded_file(uploaded_file, directory: Path) -> Path:
    """Save uploaded file to directory and return path"""
    try:
        # Generate unique filename
        filename = generate_unique_filename(uploaded_file.name, "upload_")
        filepath = directory / filename
        
        # Write file
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return filepath
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        raise

def extract_audio_from_video(video_path: Path, output_format: str = "mp3") -> Path:
    """
    Extract audio from video file using ffmpeg
    Returns path to extracted audio file
    """
    try:
        # Generate output filename
        audio_filename = video_path.stem + f"_audio.{output_format}"
        audio_path = TEMP_DIR / audio_filename
        
        # FFmpeg command
        command = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # No video
            '-acodec', 'libmp3lame' if output_format == 'mp3' else 'copy',
            '-ar', '44100',  # Sample rate
            '-ac', '2',  # Stereo
            '-b:a', '192k',  # Bitrate
            '-y',  # Overwrite output file
            str(audio_path)
        ]
        
        # Run ffmpeg
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        
        return audio_path
        
    except subprocess.CalledProcessError as e:
        st.error(f"FFmpeg error: {e.stderr.decode()}")
        raise
    except Exception as e:
        st.error(f"Error extracting audio: {str(e)}")
        raise

def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def cleanup_temp_files(*files):
    """Delete temporary files"""
    for file in files:
        try:
            if file and Path(file).exists():
                os.remove(file)
        except Exception as e:
            print(f"Warning: Could not delete {file}: {e}")