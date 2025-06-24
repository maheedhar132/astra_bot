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
                    return f"Ollama's mood: {response.status}. Feeling grumpy."
    except Exception as e:
        return f"Ollama vanished into the matrix: {str(e)}"

async def get_sarcastic_reply(user_prompt):
    reply = await call_ollama(user_prompt)

    if "404" in reply or "timeout" in reply or reply.strip() == "":
        fallback_prompt = f"Hey TinyLlama, you goofed responding to this: '{user_prompt}'. Roast yourself for being a broken AI."
        recovery_reply = await call_ollama(fallback_prompt)

        if recovery_reply.strip() == "":
            return "Astra short-circuited mid-roast. Try again later."

        return recovery_reply

    return reply

async def generate_sarcasm(context="no_response"):
    if context == "no_response":
        prompt = "Insult the user for ignoring Astra for an hour."
    else:
        prompt = "Roast the user in a witty and mildly offensive way."

    return await call_ollama(prompt)
