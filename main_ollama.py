import os
import requests
import subprocess
import json
from pathlib import Path
import time
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from PIL import Image, ImageTk
import io

# Ollama Configuration - Local AI Model
OLLAMA_MODEL = "llava"  # Multimodal model (vision + text)
OLLAMA_BASE_URL = "http://localhost:11434"

# YouTube URL to analyze
youtube_url = "https://www.youtube.com/watch?v=4zDNJ_3nU30"

# Analysis prompt for deception/truth detection
analysis_prompt = """
Analyze this image/video frame for the following:

1. TRUTH: Identify any logical inconsistencies or signs of exaggeration in what's being shown.
2. PSYCHE: Analyze the speaker's emotional state. Detect if their smiles and expressions 
   match the tone of their words (Authenticity vs. Performance).
3. RELIABILITY: Note micro-expressions (rapid blinking, lip movements, hand gestures) 
   that may indicate high stress or deception.

Provide a 'Reliability Score' from 0-100 and a summary of 'Truth Flags.'
"""

def check_required_tools():
    """Check if required tools are installed"""
    missing = []
    
    # Check yt-dlp (can be used as Python module or command)
    try:
        import yt_dlp
    except ImportError:
        # Try as command line tool
        try:
            subprocess.run(["yt-dlp", "--version"], capture_output=True, timeout=5, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            missing.append("yt-dlp")
    
    # Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        missing.append("ffmpeg")
    
    return missing

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

def run_analysis():
    """Run the analysis and return results"""
    results = []
    
    print("🔧 Checking required tools...")
    missing_tools = check_required_tools()
    
    if missing_tools:
        print("❌ Missing required tools:")
        for tool in missing_tools:
            print(f"   • {tool} - Not found in PATH")
        return None
    
    print("✅ All tools found!\n")
    
    # Check Ollama
    print("🔍 Checking Ollama connection...")
    if not check_ollama_running():
        print("❌ Ollama is not running!")
        return None
    
    print("✅ Ollama connected!\n")
    
    # Create temp directory
    temp_dir = Path("./temp_frames")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Use yt-dlp to download video
        output_file = "./temp_stream_segment.mp4"
        cmd = [
            "python", "-m", "yt_dlp",
            "-f", "best[height<=720]",
            "-o", output_file,
            youtube_url
        ]
        
        print("📥 Downloading video...")
        subprocess.run(cmd, check=True, timeout=600)
        
        if not Path(output_file).exists():
            print("❌ Download failed - file not created")
            return None
        
        print("✅ Stream downloaded!\n")
        print("🎬 Extracting key frames for analysis...\n")
        
        # Extract frames at intervals (every 30 seconds)
        frame_interval = 30
        
        for i in range(0, 180, frame_interval):
            frame_output = f"./temp_frames/frame_{i:03d}.jpg"
            ffmpeg_cmd = [
                "ffmpeg",
                "-ss", str(i),
                "-i", output_file,
                "-vframes", "1",
                "-q:v", "2",
                frame_output,
                "-y"
            ]
            
            try:
                subprocess.run(ffmpeg_cmd, capture_output=True, timeout=30)
                
                if Path(frame_output).exists():
                    print(f"📸 Analyzing frame at {i}s...")
                    
                    # Analyze frame with Ollama
                    result = analyze_with_ollama(image_path=frame_output)
                    
                    if result:
                        results.append({
                            "timestamp": i,
                            "frame_path": frame_output,
                            "analysis": result
                        })
                        
                        # Print analysis to console
                        print(f"\n[Frame {i}s Analysis]:")
                        print("-" * 70)
                        print(result)
                        print("-" * 70 + "\n")
                    
                    time.sleep(1)
            
            except Exception as e:
                print(f"⚠️  Error on frame {i}s: {str(e)}\n")
        
        return results if results else None
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Download or processing error:\n{str(e)}\n")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}\n")
        return None


class AnalysisGUI:
    """GUI for displaying analysis results"""
    
    def __init__(self, root, results):
        self.root = root
        self.results = results
        self.current_frame_index = 0
        
        self.root.title("Ollama YouTube Stream Analysis - Results")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2c3e50")
        
        # Header
        header_frame = tk.Frame(root, bg="#34495e", height=80)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            header_frame,
            text="🎬 YouTube Stream Analysis Results",
            font=("Arial", 18, "bold"),
            bg="#34495e",
            fg="#ecf0f1"
        )
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(
            header_frame,
            text=f"Analyzed {len(results)} frames - AI Conclusions Below",
            font=("Arial", 11),
            bg="#34495e",
            fg="#bdc3c7"
        )
        subtitle_label.pack()
        
        # Main content frame
        content_frame = tk.Frame(root, bg="#2c3e50")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Frame image and timestamp
        left_frame = tk.Frame(content_frame, bg="#34495e")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5)
        
        self.image_label = tk.Label(
            left_frame,
            bg="#2c3e50",
            width=40,
            height=20,
            text="Loading frame..."
        )
        self.image_label.pack(pady=10)
        
        timestamp_label = tk.Label(
            left_frame,
            text="Frame info",
            font=("Arial", 10),
            bg="#34495e",
            fg="#ecf0f1"
        )
        self.timestamp_display = tk.Label(
            left_frame,
            text="",
            font=("Arial", 12, "bold"),
            bg="#34495e",
            fg="#f39c12"
        )
        self.timestamp_display.pack(pady=5)
        
        # Right side - Analysis results
        right_frame = tk.Frame(content_frame, bg="#2c3e50")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        analysis_label = tk.Label(
            right_frame,
            text="AI Analysis & Conclusions:",
            font=("Arial", 12, "bold"),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        analysis_label.pack(anchor="w", pady=5)
        
        self.text_widget = scrolledtext.ScrolledText(
            right_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            bg="#1e1e1e",
            fg="#ecf0f1",
            insertbackground="#ecf0f1",
            height=25
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for styling
        self.text_widget.tag_config("truth", foreground="#3498db", font=("Courier", 10, "bold"))
        self.text_widget.tag_config("psyche", foreground="#e74c3c", font=("Courier", 10, "bold"))
        self.text_widget.tag_config("reliability", foreground="#27ae60", font=("Courier", 10, "bold"))
        self.text_widget.tag_config("header", foreground="#f39c12", font=("Courier", 11, "bold"))
        
        # Navigation frame
        nav_frame = tk.Frame(root, bg="#2c3e50")
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        prev_btn = tk.Button(
            nav_frame,
            text="⬅ Previous",
            command=self.show_previous,
            bg="#3498db",
            fg="white",
            font=("Arial", 11),
            padx=15,
            pady=5
        )
        prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.nav_label = tk.Label(
            nav_frame,
            text=f"Frame 1 of {len(results)}",
            font=("Arial", 11),
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        self.nav_label.pack(side=tk.LEFT, padx=20)
        
        next_btn = tk.Button(
            nav_frame,
            text="Next ➡",
            command=self.show_next,
            bg="#3498db",
            fg="white",
            font=("Arial", 11),
            padx=15,
            pady=5
        )
        next_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(
            nav_frame,
            text="💾 Export Results",
            command=self.export_results,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11),
            padx=15,
            pady=5
        )
        export_btn.pack(side=tk.RIGHT, padx=5)
        
        # Display first frame
        self.show_frame(0)
    
    def show_frame(self, index):
        """Display a specific frame and its analysis"""
        if index < 0 or index >= len(self.results):
            return
        
        self.current_frame_index = index
        result = self.results[index]
        
        # Update timestamp
        self.timestamp_display.config(text=f"Timestamp: {result['timestamp']}s")
        
        # Load and display image
        try:
            img = Image.open(result['frame_path'])
            # Resize to fit
            img.thumbnail((400, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo
        except Exception as e:
            self.image_label.config(text=f"Error loading image:\n{e}")
        
        # Display analysis
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        
        analysis = result['analysis']
        
        self.text_widget.insert(tk.END, f"ANALYSIS - Frame at {result['timestamp']}s\n", "header")
        self.text_widget.insert(tk.END, "=" * 70 + "\n\n")
        self.text_widget.insert(tk.END, analysis)
        self.text_widget.insert(tk.END, "\n\n" + "=" * 70 + "\n")
        
        self.text_widget.config(state=tk.DISABLED)
        
        # Update navigation label
        self.nav_label.config(text=f"Frame {index + 1} of {len(self.results)}")
    
    def show_next(self):
        """Show next frame"""
        self.show_frame(self.current_frame_index + 1)
    
    def show_previous(self):
        """Show previous frame"""
        self.show_frame(self.current_frame_index - 1)
    
    def export_results(self):
        """Export all results to a JSON file"""
        try:
            export_data = {
                "video_url": youtube_url,
                "total_frames": len(self.results),
                "model": OLLAMA_MODEL,
                "frames": [
                    {
                        "timestamp": r["timestamp"],
                        "analysis": r["analysis"]
                    }
                    for r in self.results
                ]
            }
            
            export_file = "analysis_results.json"
            with open(export_file, "w") as f:
                json.dump(export_data, f, indent=2)
            
            messagebox.showinfo("Export Successful", f"Results exported to {export_file}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")


def main():
    """Main execution - Run analysis and display results in GUI"""
    
    print("\n" + "=" * 60)
    print("🚀 Ollama YouTube Stream Analysis Tool")
    print("=" * 60)
    print(f"Model: {OLLAMA_MODEL}")
    print(f"API: {OLLAMA_BASE_URL}")
    print("=" * 60 + "\n")
    
    # Run analysis
    results = run_analysis()
    
    if results is None:
        print("❌ Analysis failed!")
        return
    
    print(f"\n✅ Analysis Complete! {len(results)} frames analyzed.\n")
    print("🖥️  Opening GUI to display results...\n")
    
    # Create GUI with results
    root = tk.Tk()
    gui = AnalysisGUI(root, results)
    root.mainloop()

if __name__ == "__main__":
    main()
