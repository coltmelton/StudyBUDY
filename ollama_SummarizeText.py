import requests
import time


class SummarizeText:

    def __init__(self, model="llama3:8b", base_url="http://localhost:11434"):
        #Base url and type model ollama is using based on my ram
        self.api_url = f"{base_url}/api/generate"
        self.model = model

    def test_connection(self):

        try:
            # check if ollama is responding
            test_url = self.api_url.replace('/api/generate', '/api/tags')
            response = requests.get(test_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False


    def summarize(self, text: str) -> str:

        #check if there's a script to summarize
        if not text.strip():
            return "No transcript available to summarize."

        #Check if ollama is running before attempting the request
        if not self.test_connection():
            return "Error: Cannot connect to ollama. Please ensure ollama is running locally"

        #Only allow 15,000 characters to prevent timeout
        max_characters = 15000
        if len(text) > max_characters:
            text = text[:max_characters] + "..."
            print(f"Text limited to {max_characters} characters to avoid timeout")

        #Prompt to send to ollama
        prompt = f"""
Summarize this lecture transcript into a structured, student-friendly summary.
Follow this format strictly:

**Title:**
[Short descriptive title of the lecture]

**Key Concepts:**
- Provide as many key concepts as necessary from the lecture

**Important Details / Examples:**
- Provide as many details or examples as needed to cover the content

**Summary / Takeaways:**
- Capture the most important points and overall insights from the lecture

Do not include anything outside of this format. Keep it concise, clear, and easy for a student to study from.

Lecture Transcript:
{text}
"""

        try:
            #Create JSON request to send to ollama
            request = {"model": self.model, "prompt": prompt, "stream": False,
                    "options": {
                    "temperature": 0.1,  #clear output, simpler to read and straight to the point
                    "top_p": 0.8,        #consider top 80% tokens/whole words or part of words
                    "num_ctx": 4096,     #max number of tokens the model can consider in a request
                }
            }

            print(f"Sending request to ollama...")

            #Send data to ollama
            response = requests.post(self.api_url, json=request, timeout=180)

            #Process response
            if response.status_code == 200:
                #Convert json response to python dictionary
                data = response.json()
                result = data.get("response", "").strip()

                if not result:
                    return "Error: Received empty response from ollama"
                return result
            #If http status isn't 200
            else:
                return f"HTTP Error {response.status_code}: {response.text}"

        #Throw error if it's taking too long
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The text might be too long, or ollama is taking too long to respond."
