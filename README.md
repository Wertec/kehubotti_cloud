# Kehubotti Cloud (FastAPI + Twilio) — Täydellinen asennusopas (FREE)

Kehubotti Cloud on pilvessä toimiva kehu-botti puheluille.
Se käyttää Twiliota puheluihin, Whisperiä puheentunnistukseen, GPT:tä kehuun ja TTS:ää ääneen.

## 🔧 Mitä tarvitset
- Twilio-tili + puhelinnumero (trial riittää testiin)
- OpenAI API -avain
- Render-tili (Free-taso)
- Git + Python 3

---
## 1) Kloonaa/valmistele repo
Lataa tämä kansio tai puske GitHubiin:
```bash
git init
git add .
git commit -m "Kehubotti Cloud initial"
git branch -M main
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

## 2) Paikallinen testaus
```bash
cp .env.example .env  # täytä avaimet
pip install -r requirements.txt
uvicorn main:app --reload
```
Testaa: http://127.0.0.1:8000/docs

## 3) Deploy Renderiin (FREE)
- New → Web Service → Build from Git
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host=0.0.0.0 --port=${PORT}`
- Instance Type: Free
- Aseta Environment vars:
  - OPENAI_API_KEY=sk-xxxxx
  - BASE_URL=https://<render-subdomain>.onrender.com

## 4) Twilio-kytkentä
Twilio Console → Phone Numbers → valitse numerosi → Voice →
“A CALL COMES IN” = `https://<render-subdomain>.onrender.com/voice` (POST)

## 5) Soita ja testaa
- Botti sanoo: “Hei! Miten kuuluu?”
- Twilio tallentaa ääninäytteen → Whisper STT → GPT kehu → TTS mp3
- Twilio soittaa mp3:n takaisin soittajalle

## Huomioita
- Free-taso Renderissä “nukahtaa” 15 minuutin jälkeen → ensimmäinen pyyntö herättää (20–60 s)
- Päivitä Starteriin jos haluat 24/7 hereillä
- Twilio trial lisää oman ilmoituksensa puheluun

## Turvallisuus
- Älä koskaan committaa `.env`-tiedostoa julkiseen repoosi
- Käytä HTTPS-osoitteita ja vahvoja API-avaimia
