import os
import requests
import subprocess
import json
from pathlib import Path

# Ollama Configuration - Local AI Model
OLLAMA_MODEL = "llava"  # Multimodal model (vision + text)
OLLAMA_BASE_URL = "http://localhost:11434"

# YouTube URL to analyze
youtube_url = "https://www.youtube.com/watch?v=4zDNJ_3nU30"

# Analysis prompt for deception/truth detection
analysis_prompt = """
Analyze this image/video frame for the following:

1. TRUTH: Identify any logical inconsistencies or signs of exaggeration in what's being shown.
2. FELICITY: Analyze the speaker's emotional state. Detect if their smiles and expressions 
   match the tone of their words (Authenticity vs. Performance).
3. RELIABILITY: Note micro-expressions (rapid blinking, lip movements, hand gestures) 
   that may indicate high stress or deception.

Provide a 'Reliability Score' from 0-100 and a summary of 'Truth Flags.'
"""

def check_ollama_running():
    """Check if Ollama is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def download_youtube_frame(url, frame_number=0):
    """
    Download a frame from YouTube video using yt-dlp
    Returns the frame image path
    """
    try:
        output_path = Path("./temp_frame.jpg")
        # Using yt-dlp to extract a frame
        cmd = [
            "yt-dlp",
            "--write-thumbnail",
            "-o", "%(title)s.%(ext)s",
            url
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except Exception as e:
        print(f"Error downloading YouTube frame: {e}")
        return None

def analyze_with_ollama(image_path=None, text_prompt=None):
    """
    Send image/text to Ollama for analysis
    Uses LLaVA for multimodal (vision + text) processing
    """
    if not check_ollama_running():
        print("❌ Ollama is not running!")
        print("   Install Ollama from: https://ollama.ai")
        print("   Then run: ollama serve")
        print("   In another terminal: ollama pull llava")
        return None
    
    try:
        # For multimodal: send image to LLaVA
        if image_path:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Ollama API for vision analysis
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": text_prompt or analysis_prompt,
                    "images": [image_path],
                    "stream": False
                },
                timeout=60
            )
        else:
            # Text-only analysis
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": text_prompt or analysis_prompt,
                    "stream": False
                },
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            print(f"Error: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"Error communicating with Ollama: {e}")
        return None

def main():
    """Main execution"""
    print("🎥 YouTube Video Analysis with Local Ollama AI")
    print(f"📍 Model: {OLLAMA_MODEL}")
    print(f"🔗 API: {OLLAMA_BASE_URL}\n")
    
    # Check if Ollama is running
    print("Checking Ollama connection...")
    if not check_ollama_running():
        print("❌ Ollama is not running!")
        print("\n📥 Installation steps:")
        print("1. Download Ollama from: https://ollama.ai")
        print("2. Install and run: ollama serve")
        print("3. In another terminal, pull the model: ollama pull llava")
        print("4. Then run this script again")
        return
    
    print("✅ Ollama is running!\n")
    
    # Option 1: Analyze with local image/frame
    print("Choose analysis mode:")
    print("1. Analyze local image file")
    print("2. Download YouTube frame and analyze")
    print("3. Text-only analysis (no video)")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        image_path = input("Enter image path: ").strip()
        print(f"\n🔍 Analyzing image: {image_path}")
        result = analyze_with_ollama(image_path=image_path)
    
    elif choice == "2":
        print(f"\n📥 Downloading frame from: {youtube_url}")
        # Note: Requires yt-dlp to be installed: pip install yt-dlp
        print("(Note: Requires yt-dlp. Install with: pip install yt-dlp)")
        image_path = download_youtube_frame(youtube_url)
        if image_path:
            print(f"✅ Frame saved: {image_path}")
            print(f"\n🔍 Analyzing frame...")
            result = analyze_with_ollama(image_path=str(image_path))
        else:
            print("❌ Failed to download frame")
            return
    
    elif choice == "3":
        print("\n🔍 Performing text-only analysis...")
        result = analyze_with_ollama(text_prompt=analysis_prompt)
    
    else:
        print("Invalid choice!")
        return
    
    # Display results
    if result:
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS:")
        print("="*60)
        print(result)
        print("="*60)
    else:
        print("\n❌ Analysis failed!")

if __name__ == "__main__":
    main()
