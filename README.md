# PolyLingo Voice Studio

An advanced multilingual **Speech/Text -> Translate -> Speech** app built with Streamlit.

## What it does

- Supports two workflows with a mode toggle:
  - Speech to Text
  - Text to Speech
- Accepts text in almost any language.
- Converts recorded or uploaded audio to text.
- Supports source language auto-detection.
- Translates from one source language to one or many target languages.
- Generates speech (MP3) for each translated result.
- Lets you play and download audio per language.

## Tech stack

- Streamlit (UI)
- deep-translator (Google Translate wrapper)
- edge-tts (high-quality neural TTS voices)
- SpeechRecognition (speech-to-text)

## Setup

```
pip install -r requirements.txt
```

## Run

```
streamlit run app.py
```

Then open the local URL shown by Streamlit.

## How to use

1. Choose a workflow mode at the top:
   - `Speech to Text` for transcription.
   - `Text to Speech` for translation + audio generation.
2. Select source language (or use `Auto Detect`).
3. Select one or more target languages.
4. For Speech to Text mode:
   - Record audio using the microphone input, or upload a supported audio file.
   - Click `Transcribe Audio`.
   - The transcribed text is saved and can be reused in Text to Speech mode.
5. For Text to Speech mode:
   - Enter text (or use transcribed text from STT mode).
   - Click `Translate + Generate Speech`.
   - Play or download each generated MP3.

## Audio input support

- Microphone recording via Streamlit audio input.
- Upload formats: WAV, FLAC, AIFF/AIF/AIFC, MP3, MP4, MPEG.

## FFmpeg requirement for MP3/MP4/MPEG

- WAV/FLAC/AIFF uploads work directly with SpeechRecognition.
- MP3/MP4/MPEG are converted to WAV before transcription.
- For this conversion, FFmpeg must be installed and available in your system PATH.

## Notes

- Internet access is required for translation, speech recognition, and speech generation.
- Speech recognition uses an online recognizer.
- If a language has no exact matching voice, the app falls back to a multilingual English neural voice.
