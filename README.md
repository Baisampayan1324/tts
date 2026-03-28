# PolyLingo Voice Studio

An advanced multilingual **Text -> Translate -> Speech** app.

## What it does

- Accepts text in almost any language.
- Converts recorded speech to text.
- Supports source language auto-detection.
- Translates to one or many target languages at once.
- Generates speech (MP3) for each translated result.
- Lets you play and download audio per language.

## Tech stack

- Streamlit (UI)
- deep-translator (Google Translate wrapper)
- edge-tts (high-quality neural TTS voices)
- SpeechRecognition (speech-to-text)

## Setup

```powershell
cd p:\tts
C:/Users/BAISAMPAYAN/AppData/Local/Programs/Python/Python311/python.exe -m pip install -r requirements.txt
```

## Run

```powershell
cd p:\tts
C:/Users/BAISAMPAYAN/AppData/Local/Programs/Python/Python311/python.exe -m streamlit run app.py
```

Then open the local URL shown by Streamlit.

## Notes

- Internet access is required for translation and speech generation.
- Speech recognition uses an online recognizer.
- If a language has no exact matching voice, the app falls back to a multilingual English neural voice.
