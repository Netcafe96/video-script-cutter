# streamlit_app.py
import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip
import whisper
import difflib
from typing import List, Tuple

# -------------------------------
# Speech-to-text with whisper
# -------------------------------
def transcribe_audio(video_path: str) -> List[dict]:
    model = whisper.load_model("base")
    result = model.transcribe(video_path, verbose=False)
    return result['segments']

# -------------------------------
# Fuzzy match full script to transcript window
# -------------------------------
def match_summary_to_transcript(script: str, segments: List[dict], window_size: int = 3) -> Tuple[float, float]:
    best_score = 0.0
    best_range = (0.0, 0.0)

    for i in range(len(segments) - window_size + 1):
        window_segments = segments[i:i+window_size]
        window_text = " ".join([seg['text'] for seg in window_segments])
        score = difflib.SequenceMatcher(None, script.lower(), window_text.lower()).ratio()
        if score > best_score:
            best_score = score
            best_range = (window_segments[0]['start'], window_segments[-1]['end'])

    return best_range

# -------------------------------
# Cut video segment
# -------------------------------
def cut_video_segment(video_path: str, start: float, end: float) -> str:
    clip = VideoFileClip(video_path)
    subclip = clip.subclip(start, end)
    output_path = os.path.join(tempfile.gettempdir(), "summary_segment.mp4")
    subclip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)
    return output_path

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("🎬 Cắt Video Từ Kịch Bản Tóm Tắt")

video_file = st.file_uploader("Tải lên video (.mp4)", type=["mp4"])
script_text = st.text_area("Dán kịch bản tóm tắt vào đây:")

if st.button("🔍 Tìm và Cắt đoạn khớp") and video_file and script_text:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(video_file.read())
        tmp_video_path = tmp_video.name

    with st.spinner("🧠 Đang chuyển giọng nói thành văn bản..."):
        segments = transcribe_audio(tmp_video_path)

    with st.spinner("🔎 Đang so khớp kịch bản với lời thoại..."):
        start, end = match_summary_to_transcript(script_text.strip(), segments)

    if start == end:
        st.error("Không tìm được đoạn nào khớp đáng kể với kịch bản.")
    else:
        with st.spinner("✂️ Đang cắt đoạn video khớp..."):
            output_path = cut_video_segment(tmp_video_path, start, end)
        st.success("Đã cắt xong đoạn video phù hợp!")

        with open(output_path, "rb") as f:
            st.download_button(
                label="📥 Tải đoạn video khớp",
                data=f,
                file_name="video_tomtat.mp4",
                mime="video/mp4"
            )
