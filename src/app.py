import streamlit as st
from dotenv import load_dotenv
import os
from pathlib import Path

# Import Google processor
from config import (
    MAX_FILE_SIZE_MB, 
    SUPPORTED_VIDEO_FORMATS, 
    SUPPORTED_AUDIO_FORMATS,
    TEMP_DIR
)
from utils import save_uploaded_file, is_video_file, is_audio_file, cleanup_temp_files, format_timestamp
from google_processor import process_media_file, GeminiProcessor

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Smart Video Summarizer",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state
if 'transcripts' not in st.session_state:
    st.session_state.transcripts = []

# Title
st.title("🎓 Smart Video Summarizer")
st.subheader("AI-Powered Study Assistant")

# Sidebar
with st.sidebar:
    st.header("📁 Upload Your Materials")
    
    # API Key check
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ Google API Key Missing!")
        st.info("Get your free key at: https://aistudio.google.com/app/apikey")
        st.stop()
    else:
        st.success("✅ Google API Key Loaded")
    
    st.markdown("---")
    
    # File uploader
    st.subheader("Upload Media Files")
    st.info(f"**Supported formats:**\n"
            f"📹 Video: {', '.join(SUPPORTED_VIDEO_FORMATS)}\n"
            f"🎵 Audio: {', '.join(SUPPORTED_AUDIO_FORMATS)}")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=[fmt.replace('.', '') for fmt in SUPPORTED_VIDEO_FORMATS + SUPPORTED_AUDIO_FORMATS],
        help=f"Max file size: {MAX_FILE_SIZE_MB}MB"
    )
    
    # Process button
    process_button = st.button("🚀 Process File", type="primary", use_container_width=True)
    
    st.markdown("---")
    st.caption("💡 Powered by Google Gemini 1.5 Flash")
    st.caption("⚡ FREE tier: 15 req/min, 1500 req/day")

# Main area (Right wala Area)
if not uploaded_file:

    st.markdown("---")
    st.markdown("### Welcome! 👋")
    st.markdown("""
    Usecases:
    - 📹 **Transcribe lecture videos** - Get text from any video
    - 🎵 **Convert audio to text** - Transcribe recordings automatically
    - 📝 **Summarize content** - Get brief or detailed summaries
    - 📊 **Generate study guides** - Create study materials automatically
    
    **Get started by uploading a video or audio file! →**
    """)
    

    # Example use cases
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("**📚 Lecture Recording**\n\nUpload your recorded lecture to get a full transcript")
    
    with col2:
        st.success("**🎬 Educational Video**\n\nProcess educational videos to extract key points")
    
    with col3:
        st.success("**🎙️ Podcast/Interview**\n\nTranscribe discussions for easy reference")

else:
    # File uploaded
    st.markdown("---")
    
    # Display file info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📄 Filename", uploaded_file.name)
    
    with col2:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.metric("📦 Size", f"{file_size_mb:.2f} MB")
    
    with col3:
        file_type = "Video 📹" if is_video_file(uploaded_file.name) else "Audio 🎵"
        st.metric("📋 Type", file_type)
    
    # Check file size
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"❌ File too large! Maximum size is {MAX_FILE_SIZE_MB}MB")
        st.stop()
    
    # Process file
    if process_button:
        try:
            with st.spinner("Processing your file with Google Gemini..."):
                # Save uploaded file
                file_path = save_uploaded_file(uploaded_file, TEMP_DIR)
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process the file
                status_text.text("🔄 Starting processing...")
                progress_bar.progress(20)
                
                # Call processor
                transcript_data = process_media_file(file_path, api_key)
                
                progress_bar.progress(80)
                
                # Save transcript
                processor = GeminiProcessor(api_key)
                saved_path = processor.save_transcript(transcript_data)
                
                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")
                
                # Add to session state
                st.session_state.transcripts.append(transcript_data)
                
                # Cleanup
                cleanup_temp_files(file_path)
                
                st.success(f"✅ Transcript saved to: {saved_path.name}")
                st.balloons()
                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.exception(e)

# Display transcripts
if st.session_state.transcripts:
    st.markdown("---")
    st.markdown("## 📝 Transcripts")
    
    for idx, transcript in enumerate(st.session_state.transcripts):
        with st.expander(
            f"📄 {transcript.get('original_file', 'Unknown')} - {transcript.get('media_type', 'Unknown').title()}", 
            expanded=(idx == len(st.session_state.transcripts) - 1)
        ):
            
            # Metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🤖 Model", transcript.get('model', 'Gemini'))
            with col2:
                word_count = transcript.get('word_count', len(transcript.get('text', '').split()))
                st.metric("📊 Words", f"{word_count:,}")
            with col3:
                st.metric("🌍 Language", transcript.get('language', 'Auto').upper())
            
            st.markdown("---")
            
            # Transcript text
            st.markdown("### Full Transcript:")
            transcript_text = transcript.get('text', '')
            st.text_area(
                "Transcript",
                transcript_text,
                height=300,
                key=f"transcript_{idx}",
                label_visibility="collapsed"
            )
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="💾 Download Transcript",
                    data=transcript_text,
                    file_name=f"transcript_{transcript.get('original_file', 'file')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # Summarize button
                if st.button("✨ Generate Summary", key=f"summarize_{idx}", use_container_width=True):
                    with st.spinner("Generating summary with Gemini..."):
                        processor = GeminiProcessor(api_key)
                        summary = processor.summarize_text(transcript_text, "study_guide")
                        st.session_state[f'summary_{idx}'] = summary
            
            # Display summary if generated
            if f'summary_{idx}' in st.session_state:
                st.markdown("---")
                st.markdown("### 📚 Study Guide Summary:")
                st.markdown(st.session_state[f'summary_{idx}'])

