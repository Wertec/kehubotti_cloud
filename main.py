from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.get("/")
async def root():
    return {"message": "Kehubotti on käynnissä!"}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")

    if not user_message:
        return JSONResponse({"reply": "Kirjoita jotain ensin!"})

    # OpenAI API-kutsu
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "Olet ystävällinen kehubotti, joka antaa kehuja ja hyvää mieltä."},
                        {"role": "user", "content": user_message}
                    ],
                },
                timeout=30.0
            )

        result = response.json()
        reply = result["choices"][0]["message"]["content"].strip()
        return {"reply": reply}

    except Exception as e:
        return {"reply": f"Virhe OpenAI-yhteydessä: {e}"}

@app.get("/health")
async def health():
    return {"status": "OK"}
