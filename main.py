
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse, Response, FileResponse
import httpx, os, uuid
from pathlib import Path
from dotenv import load_dotenv

# --- Lataa ympäristömuuttujat ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://kehubotti-cloud.onrender.com")

# --- Alustukset ---
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # salli kaikki domainit testauksen ajaksi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

# --- Yleinen testireitti ---
@app.get("/")
async def root():
    return {"message": "Kehubotti on käynnissä!"}

@app.get("/health")
async def health():
    return {"status": "OK"}

# --- CHAT (selaintesti) ---
@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")

    if not user_message:
        return JSONResponse({"reply": "Kirjoita jotain ensin!"})

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
                        {"role": "system", "content": "Olet ystävällinen ja empaattinen kehubotti, joka antaa kehuja ja positiivisia kommentteja suomeksi."},
                        {"role": "user", "content": user_message}
                    ],
                },
                timeout=30.0
            )

        # Tulostetaan tarkalleen mitä OpenAI palauttaa (debug)
        result = response.json()
        print("DEBUG OpenAI vastaus:", result)

        if "error" in result:
            err = result["error"].get("message", "Tuntematon virhe")
            return {"reply": f"Virhe OpenAI-yhteydessä: {err}"}

        choices = result.get("choices")
        if not choices:
            return {"reply": f"Virhe OpenAI-yhteydessä: ei sisältöä ({result})"}

        reply = choices[0]["message"]["content"].strip()
        return {"reply": reply}

    except Exception as e:
        return {"reply": f"Virhe OpenAI-yhteydessä: {e}"}

    data = await request.json()
    user_message = data.get("message", "")

    if not user_message:
        return JSONResponse({"reply": "Kirjoita jotain ensin!"})

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
                        {"role": "system", "content": "Olet ystävällinen ja empaattinen kehubotti, joka antaa lyhyitä kehuja ja positiivisia kommentteja suomeksi."},
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


# --- TWILIO: Puhelinäänet ---
def twiml(body: str) -> Response:
    return Response(content=body.strip(), media_type="application/xml")

@app.post("/voice")
async def voice():
    return twiml("""
<Response>
  <Say language="fi-FI">Hei! Miten kuuluu? Kerro minulle lyhyesti.</Say>
  <Record action="/process_recording" maxLength="8" playBeep="false"/>
  <Say language="fi-FI">En kuullut mitään. Yritetään uudelleen.</Say>
  <Redirect>/voice</Redirect>
</Response>
""")

@app.post("/process_recording")
async def process_recording(request: Request, background: BackgroundTasks):
    form = await request.form()
    recording_url = form.get("RecordingUrl")
    rid = str(uuid.uuid4())
    in_path = STATIC_DIR / f"{rid}.wav"
    out_path = STATIC_DIR / f"{rid}_reply.mp3"
    background.add_task(process_pipeline, recording_url, in_path, out_path)
    audio_url = f"{BASE_URL}/static/{out_path.name}"
    return twiml(f"""
<Response>
  <Pause length="2"/>
  <Play>{audio_url}</Play>
  <Redirect>/voice</Redirect>
</Response>
""")

async def process_pipeline(recording_url: str, in_path: Path, out_path: Path):
    async with httpx.AsyncClient() as client:
        r = await client.get(recording_url + ".wav")
        in_path.write_bytes(r.content)
    text = await whisper_stt(in_path)
    compliment = await gpt_reply(text)
    audio_bytes = await tts_mp3(compliment)
    out_path.write_bytes(audio_bytes)

async def whisper_stt(path: Path) -> str:
    import aiohttp
    data = aiohttp.FormData()
    data.add_field("file", path.read_bytes(), filename=path.name, content_type="audio/wav")
    data.add_field("model", "whisper-1")
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    async with aiohttp.ClientSession() as s:
        async with s.post("https://api.openai.com/v1/audio/transcriptions", data=data, headers=headers) as resp:
            j = await resp.json()
    return j.get("text", "") or "(hiljaisuus)"

async def gpt_reply(user_text: str) -> str:
    import aiohttp
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role":"system","content":"Olet empaattinen ja positiivinen kehubotti suomeksi, vastaa lyhyesti ja rohkaisevasti."},
            {"role":"user","content": f"Soittaja sanoi: {user_text}"}
        ]
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as s:
        async with s.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers) as resp:
            j = await resp.json()
    return j["choices"][0]["message"]["content"].strip()

async def tts_mp3(text: str) -> bytes:
    import aiohttp
    payload = {"model":"gpt-4o-mini-tts","voice":"alloy","input":text}
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as s:
        async with s.post("https://api.openai.com/v1/audio/speech", json=payload, headers=headers) as resp:
            return await resp.read()

@app.get("/static/{name}")
async def static_files(name: str):
    return FileResponse(STATIC_DIR / name)
