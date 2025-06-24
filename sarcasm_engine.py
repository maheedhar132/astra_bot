import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "tinyllama"

def call_ollama(prompt):
    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()
        else:
            # When API returns an error status
            return f"Ollama's mood: {response.status_code}. Feeling grumpy."
    except requests.exceptions.RequestException as e:
        return f"Ollama vanished into the matrix: {str(e)}"

def generate_response(user_prompt):
    reply = call_ollama(user_prompt)

    if "404" in reply or "timeout" in reply or reply.strip() == "":
        # Something’s wrong — Astra will self-prompt
        fallback_prompt = f"Hey TinyLlama, you goofed responding to this: '{user_prompt}'. Roast yourself for being a broken AI."
        recovery_reply = call_ollama(fallback_prompt)

        if recovery_reply.strip() == "":
            # Even fallback failed, return last-resort line
            return "Astra short-circuited mid-roast. Try again later."
        
        return recovery_reply

    return reply

def generate_sarcasm(context="no_response"):
    if context == "no_response":
        prompt = "Insult the user for ignoring Astra for an hour."
    else:
        prompt = "Roast the user in a witty and mildly offensive way."

    return call_ollama(prompt)

