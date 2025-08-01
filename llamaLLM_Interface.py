import os
import requests

def call_llama(prompt: str) -> str:
    api_key = os.getenv("LLAMA_API_KEY")
    api_url = 'https://api.your-llama-provider.com/v1/chat/completions'

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3-8b",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }

    response = requests.post(api_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
