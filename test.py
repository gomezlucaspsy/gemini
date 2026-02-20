mport os
from google import genai

# This pulls the key from your environment variables
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-3.1-flash", 
    contents="Hello! Are you ready to analyze the Senate for me?"
)

print(response.text)