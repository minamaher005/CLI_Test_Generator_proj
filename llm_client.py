from ollama import Client
import os
from dotenv import load_dotenv
load_dotenv()
client = Client(
    host="https://ollama.com",
    headers={'Authorization': 'Bearer ' + os.environ.get('OLLAMA_API_KEY')}
)
## generate the .py test file:
def test_file(prompt: str, filename:str):
    print("[test_file] Sending prompt to Gemini...")
    try:
        response = client.chat(
            model='qwen3-coder-next',
            options={'temperature': 0},
            messages=[{'role': 'user', 'content': prompt}]
        )
    except Exception as e:
        print(f"[test_file] An error occurred: {e}")
        return
    print("[test_file] Got response from Gemini.")
    ## the generated code is in response.content
    try:
        with open(f"{filename}_test.py", "w") as f:
            f.write(response['message']['content'])
    except Exception as e:
        print(f"[test_file] Error writing to file: {e}")
        return
    print(f"[test_file] File '{filename}_test.py' has been created successfully!")
