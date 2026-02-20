from google import genai
from google.genai import types

# Initialize the Gemini Client
# Use gemini-3.1-pro for the best psychological/logical analysis
client = genai.Client(api_key="YOUR_API_KEY")

# The YouTube URL you want to watch (Senate Hearing, News, etc.)
youtube_url = "https://www.youtube.com/watch?v=4zDNJ_3nU30"

# The "System Prompt" defines the AI's persona as your Truth/Felicity watcher
analysis_prompt = """
Analyze this YouTube video for the following:
1. TRUTH: Cross-reference the speaker's claims with known facts. Identify logical 
   inconsistencies or contradictions compared to previous public statements.
2. FELICITY: Analyze the speaker's emotional state. Detect if their smiles 
   and expressions match the tone of their words (Authenticity vs. Performance).
3. RELIABILITY: Note micro-expressions (rapid blinking, lip-touching) or vocal 
   hesitations (pitch shifts) that may indicate high stress or deception.

Provide a 'Reliability Score' from 0-100 and a summary of 'Truth Flags.'
"""

# Send the request
response = client.models.generate_content(
    model="gemini-3.1-pro",
    contents=[
        types.Part.from_uri(
            file_uri=youtube_url,
            mime_type="video/mp4" # Gemini treats the YT stream as a video part
        ),
        analysis_prompt
    ]
)
