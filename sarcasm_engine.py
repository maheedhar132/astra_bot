import aiohttp
import asyncio

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "tinyllama"

async def call_ollama(prompt):
    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(OLLAMA_API_URL, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "").strip()
                else:
                    return f"Ollama mood: {response.status}. Feeling grumpy."
    except Exception:
        return None

async def get_sarcastic_reply(user_prompt):
    reply = await call_ollama(user_prompt)

    if not reply:
        # fallback
        fallback_prompt = f"Hey TinyLlama, you glitched while responding to: '{user_prompt}'. Roast yourself for being broken."
        recovery_reply = await call_ollama(fallback_prompt)

        if not recovery_reply:
            return "Astra short-circuited mid-roast. Try again later."

        return recovery_reply

    return reply

async def generate_sarcasm(context="no_response"):
    if context == "no_response":
        prompt = "Insult the user for ignoring Astra for an hour."
    else:
        prompt = "Roast the user in a witty and mildly offensive way."

    reply = await call_ollama(prompt)
    return reply if reply else "TinyLlama fell asleep again."
