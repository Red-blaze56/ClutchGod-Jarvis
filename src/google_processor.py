"""
Google Gemini-based processing for audio and text
"""
from pathlib import Path
from typing import Dict, Optional
import streamlit as st
import google.genai as genai
from google.genai import types
from config import GEMINI_MODEL, OUTPUT_DIR
from utils import (
    is_video_file, 
    is_audio_file, 
    extract_audio_from_video,
    cleanup_temp_files
)
import json
from datetime import datetime

class GeminiProcessor:
    """Process audio and video files using Google Gemini"""
    
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        print("CLIENT CLASS =", type(self.client)) 
        print("MODELS CLIENT =", type(self.client.models))
    
    def transcribe_audio(self, audio_path: Path) -> Dict:
        """
        Transcribe audio file using Gemini
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dict with transcript and metadata
        """
        try:
            # Upload audio file to Gemini
            st.info("📤 Uploading audio to Gemini...")
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            
            st.info("🎤 Transcribing with Gemini AI...")
            
            # Create prompt for transcription
            prompt = """
            Please transcribe this audio file accurately. 
            Provide a clean, well-formatted transcript with proper punctuation.
            Do not add any commentary, just the transcription.
            """
            
            # Generate transcription
            response = self.client.models.generate_content(
                model = GEMINI_MODEL,
                contents = [
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(
                        data = audio_bytes,
                        mime_type = "audio/mp3" 
                    )
                ]
            )

            
            # Get the text
            transcript_text = response.text
            
            # Get file info
            import os
            file_stats = os.stat(audio_path)
            
            result = {
                "text": transcript_text,
                "language": "auto-detected",
                "duration": None,  # Gemini doesn't provide duration directly
                "word_count": len(transcript_text.split()),
                "processed_at": datetime.now().isoformat(),
                "source_file": audio_path.name,
                "model": GEMINI_MODEL
            }
        
            
            return result
            
        except Exception as e:
            st.error(f"Transcription error: {str(e)}")
            raise
    
    def process_video(self, video_path: Path) -> Dict:
        """
        Process video: extract audio and transcribe
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dict with transcript and metadata
        """
        audio_path = None
        
        try:
            # Step 1: Extract audio
            st.info("🎬 Extracting audio from video...")
            audio_path = extract_audio_from_video(video_path)
            st.success("✅ Audio extracted!")
            
            # Step 2: Transcribe
            result = self.transcribe_audio(audio_path)
            result["media_type"] = "video"
            result["original_file"] = video_path.name
            st.success("✅ Transcription complete!")
            
            return result
            
        finally:
            # Cleanup temporary audio file
            if audio_path:
                cleanup_temp_files(audio_path)
    
    def process_audio(self, audio_path: Path) -> Dict:
        """
        Process audio file: transcribe directly
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dict with transcript and metadata
        """
        try:
            result = self.transcribe_audio(audio_path)
            result["media_type"] = "audio"
            result["original_file"] = audio_path.name
            st.success("✅ Transcription complete!")
            
            return result
            
        except Exception as e:
            st.error(f"Error processing audio: {str(e)}")
            raise
    
    def summarize_text(self, text: str, summary_type: str = "brief") -> str:
        """
        Summarize text using Gemini
        
        Args:
            text: Text to summarize
            summary_type: Type of summary (brief, detailed, study_guide)
        
        Returns:
            Summary text
        """
        try:
            prompts = {
                "brief": """
                Provide a brief summary of the following text in 3-5 sentences.
                Focus on the main points and key takeaways.
                """,
                "detailed": """
                Provide a detailed summary of the following text.
                Include all important concepts, examples, and explanations.
                Format it as clear bullet points or paragraphs.
                """,
                "study_guide": """
                Create a study guide from the following text for college students.
                Include:
                - Key concepts and definitions
                - Important points to remember
                - Examples if mentioned
                - Potential exam questions
                
                Format it clearly with sections and bullet points.
                """
            }
            
            prompt = prompts.get(summary_type, prompts["brief"])
            full_prompt = f"{prompt}\n\nText to summarize:\n{text}"
            
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[types.Part.from_text(text=full_prompt)]
            )
            return response.text
            
        except Exception as e:
            st.error(f"Summarization error: {str(e)}")
            raise
    
    def save_transcript(self, transcript_data: Dict, filename: str = None) -> Path:
        """
        Save transcript to JSON file
        
        Args:
            transcript_data: Transcript dictionary
            filename: Optional custom filename
        
        Returns:
            Path to saved file
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                source = transcript_data.get("original_file", "unknown")
                filename = f"transcript_{Path(source).stem}_{timestamp}.json"
            
            filepath = OUTPUT_DIR / filename
            
            # Save as JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            return filepath
            
        except Exception as e:
            st.error(f"Error saving transcript: {str(e)}")
            raise

def process_media_file(file_path: Path, api_key: str) -> Dict:
    """
    Main function to process any media file (video or audio) using Gemini
    
    Args:
        file_path: Path to media file
        api_key: Google API key
    
    Returns:
        Dict with transcript and metadata
    """
    processor = GeminiProcessor(api_key)
    
    if is_video_file(file_path.name):
        return processor.process_video(file_path)
    elif is_audio_file(file_path.name):
        return processor.process_audio(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")