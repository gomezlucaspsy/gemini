import os
from google import genai
from google.genai import types
import tkinter as tk
from tkinter import scrolledtext

# Initialize the Gemini Client
# Use gemini-2.5-flash for the best psychological/logical analysis
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")
client = genai.Client(api_key=api_key)

# The YouTube URL you want to watch (Senate Hearing, News, etc.)
youtube_url = "https://www.youtube.com/watch?v=4zDNJ_3nU30"

# The "System Prompt" defines the AI's persona as your Truth watcher
analysis_prompt = """
Analyze this YouTube video for the following:
1. TRUTH: Cross-reference the speaker's claims with known facts. Identify logical 
   inconsistencies or contradictions compared to previous public statements.
2. PSYCHE: Analyze the speaker's emotional state. Detect if their smiles 
   and expressions match the tone of their words (Authenticity vs. Performance).
3. RELIABILITY: Note micro-expressions (rapid blinking, lip-touching) or vocal 
   hesitations (pitch shifts) that may indicate high stress or deception.

Provide a 'Reliability Score' from 0-100 and a summary of 'Truth Flags.'
"""

# Send the request
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_uri(
            file_uri=youtube_url,
            mime_type="video/mp4" # Gemini treats the YT stream as a video part
        ),
        analysis_prompt
    ]
)

# Display the response in a GUI window
root = tk.Tk()
root.title("Gemini Analysis - Truth Watcher")
root.geometry("900x700")

# Create a frame for the title
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

# Create a scrolled text widget to display the response
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

# Insert the response text
text_widget.insert(tk.END, response.text)
text_widget.config(state=tk.DISABLED)  # Make read-only

# Create a frame for buttons
button_frame = tk.Frame(root, bg="#ecf0f1")
button_frame.pack(fill=tk.X, padx=10, pady=10)

# Close button
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
