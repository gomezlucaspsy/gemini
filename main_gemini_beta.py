import os
import tkinter as tk
from tkinter import scrolledtext
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai

# ==============================
# Initialize Gemini Client
# ==============================

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

client = genai.Client(api_key=api_key)

# ==============================
# YouTube URL
# ==============================

youtube_url = "https://www.youtube.com/watch?v=V4ccBEBpUMg"

def extract_video_id(url):
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL")

# ==============================
# Analysis Prompt
# ==============================

analysis_prompt = """
Analyze this transcript for:

1. TRUTH:
- Identify strong factual claims.
- Flag logical inconsistencies or contradictions.
- Highlight emotionally manipulative framing.

2. PSYCHE:
- Analyze emotional tone based on language.
- Detect defensiveness, projection, exaggeration, or stress indicators.

3. RELIABILITY:
- Based ONLY on linguistic signals,
  estimate a reliability score from 0-100.

Provide:
- A structured report
- A final 'Reliability Score'
- A list of 'Truth Flags'
"""

# ==============================
# Transcript + Language Fallback
# ==============================

def get_transcript_text(video_id):
    api = YouTubeTranscriptApi()

    try:
        # Try English first
        transcript = api.fetch(video_id, languages=['en'])
        language_used = "en"
    except:
        # Fallback to Spanish
        transcript = api.fetch(video_id, languages=['es'])
        language_used = "es"

    full_text = " ".join([entry.text for entry in transcript])
    return full_text, language_used

# ==============================
# Main Analysis
# ==============================

def analyze_video():
    try:
        video_id = extract_video_id(youtube_url)

        full_text, language_used = get_transcript_text(video_id)

        # Limit size (avoid token overflow)
        max_chars = 15000
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n\n[Transcript truncated]"

        # If Spanish, translate first
        if language_used == "es":
            translation_prompt = "Translate the following Spanish transcript into English accurately:\n\n" + full_text

            translation_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=translation_prompt
            )

            full_text = translation_response.text

        # Now analyze in English
        final_prompt = analysis_prompt + "\n\nTRANSCRIPT:\n" + full_text

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=final_prompt
        )

        return response.text

    except Exception as e:
        return f"Error occurred:\n\n{str(e)}"

# ==============================
# GUI
# ==============================

root = tk.Tk()
root.title("Gemini Analysis - Truth Watcher")
root.geometry("900x700")

title_frame = tk.Frame(root, bg="#2c3e50", height=60)
title_frame.pack(fill=tk.X)

title_label = tk.Label(
    title_frame,
    text="YouTube Analysis Report",
    font=("Arial", 16, "bold"),
    bg="#2c3e50",
    fg="white"
)
title_label.pack(pady=10)

text_widget = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    font=("Courier", 10),
    bg="#ecf0f1",
    fg="#2c3e50",
    padx=10,
    pady=10
)
text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

def run_analysis():
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, "Extracting transcript and analyzing...\nPlease wait...\n")
    root.update()

    result = analyze_video()

    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, result)
    text_widget.config(state=tk.DISABLED)

button_frame = tk.Frame(root, bg="#ecf0f1")
button_frame.pack(fill=tk.X, padx=10, pady=10)

analyze_button = tk.Button(
    button_frame,
    text="Analyze Video",
    command=run_analysis,
    bg="#27ae60",
    fg="white",
    font=("Arial", 10),
    padx=20,
    pady=5
)
analyze_button.pack(side=tk.LEFT)

close_button = tk.Button(
    button_frame,
    text="Close",
    command=root.quit,
    bg="#3498db",
    fg="white",
    font=("Arial", 10),
    padx=20,
    pady=5
)
close_button.pack(side=tk.RIGHT)

root.mainloop()