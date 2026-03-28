import asyncio
import importlib
from io import BytesIO
from typing import Any, Dict, List, Tuple

import edge_tts
import streamlit as st
from deep_translator import GoogleTranslator
from deep_translator.constants import GOOGLE_LANGUAGES_TO_CODES

Voice = Dict[str, str]
VoiceIndex = Dict[str, List[Voice]]


def get_google_languages() -> Dict[str, str]:
    """Return display-name -> language-code mapping supported by Google Translate."""
    # Use canonical mapping to avoid runtime/stub mismatches from get_supported_languages.
    return {name.title(): code for name, code in GOOGLE_LANGUAGES_TO_CODES.items()}


def get_edge_voices() -> List[Voice]:
    """Fetch the full list of available Edge TTS voices."""
    raw = asyncio.run(edge_tts.list_voices())
    voices: List[Voice] = []
    for item in raw:
        if isinstance(item, dict):
            normalized: Voice = {str(k): str(v) for k, v in item.items()}
            voices.append(normalized)
    return voices


def build_voice_index(voices: List[Voice]) -> VoiceIndex:
    """Group voices by two-letter language code (ex: 'en', 'fr')."""
    by_lang: VoiceIndex = {}
    for voice in voices:
        locale = voice.get("Locale", "")
        lang = locale.split("-")[0].lower()
        by_lang.setdefault(lang, []).append(voice)
    return by_lang


def pick_voice(language_code: str, by_lang: VoiceIndex) -> str:
    """Pick a sensible default voice for a given language code."""
    candidates = by_lang.get(language_code.lower(), [])
    if not candidates:
        # Fall back to multilingual English voice when exact language is unavailable.
        return "en-US-AvaMultilingualNeural"

    # Prefer neural voices, then female, then first available.
    neural = [v for v in candidates if "Neural" in v.get("ShortName", "")]
    female = [v for v in neural if v.get("Gender", "").lower() == "female"]

    if female:
        return female[0]["ShortName"]
    if neural:
        return neural[0]["ShortName"]
    return candidates[0]["ShortName"]


async def synthesize_audio_bytes(text: str, voice: str, rate: str, pitch: str) -> bytes:
    """Generate MP3 bytes from text using Edge TTS."""
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    out = BytesIO()
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            data = chunk.get("data")
            if isinstance(data, (bytes, bytearray)):
                out.write(data)
    return out.getvalue()


def speech_locale_hint(source_language_name: str, language_map: Dict[str, str]) -> str:
    """Convert selected source language into a speech-recognition locale hint."""
    if source_language_name == "Auto Detect":
        return "en-US"

    code = language_map.get(source_language_name, "en")
    locale_overrides = {
        "en": "en-US",
        "es": "es-ES",
        "fr": "fr-FR",
        "de": "de-DE",
        "hi": "hi-IN",
        "it": "it-IT",
        "ja": "ja-JP",
        "ko": "ko-KR",
        "pt": "pt-BR",
        "ru": "ru-RU",
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
    }

    return locale_overrides.get(code.lower(), "en-US")


def transcribe_audio(audio_bytes: bytes, locale: str) -> str:
    """Transcribe WAV audio bytes using Google Speech Recognition."""
    sr = importlib.import_module("speech_recognition")
    recognizer = sr.Recognizer()
    with sr.AudioFile(BytesIO(audio_bytes)) as source:
        audio_data = recognizer.record(source)
    recognize_google = getattr(recognizer, "recognize_google", None)
    if not callable(recognize_google):
        raise RuntimeError("SpeechRecognition recognizer is missing recognize_google")
    return str(recognize_google(audio_data, language=locale))


def translate_text(text: str, source: str, target: str) -> str:
    translator = GoogleTranslator(source=source, target=target)
    return translator.translate(text)


def run_pipeline(
    text: str,
    source_code: str,
    target_codes: List[Tuple[str, str]],
    by_lang: VoiceIndex,
    rate: str,
    pitch: str,
) -> List[Tuple[str, str, str, bytes]]:
    """
    For each target language, return:
    (display_language_name, language_code, translated_text, mp3_bytes).
    """
    results: List[Tuple[str, str, str, bytes]] = []

    for display_name, target_code in target_codes:
        translated = translate_text(text=text, source=source_code, target=target_code)
        voice = pick_voice(target_code, by_lang)
        audio_bytes = asyncio.run(synthesize_audio_bytes(translated, voice, rate, pitch))
        results.append((display_name, target_code, translated, audio_bytes))

    return results


st.set_page_config(page_title="PolyLingo Voice Studio", page_icon="🗣️", layout="wide")

st.markdown(
    """
    <style>
    .hero {
        padding: 1.1rem 1.2rem;
        border-radius: 14px;
        background: linear-gradient(120deg, #e8f5e9 0%, #e3f2fd 45%, #fffde7 100%);
        border: 1px solid #c7d2fe;
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 1.8rem;
        color: #0f172a;
    }
    .hero p {
        margin: 0.25rem 0 0;
        color: #334155;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>PolyLingo Voice Studio</h1>
      <p>Switch between speech-to-text capture and multilingual text-to-speech generation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Voice Settings")
    rate = st.select_slider(
        "Voice Speed",
        options=["-30%", "-20%", "-10%", "+0%", "+10%", "+20%", "+30%"],
        value="+0%",
    )
    pitch = st.select_slider(
        "Voice Pitch",
        options=["-20Hz", "-10Hz", "+0Hz", "+10Hz", "+20Hz"],
        value="+0Hz",
    )
    st.caption("These settings apply to all generated speech outputs.")

if "language_map" not in st.session_state:
    with st.spinner("Loading language and voice catalogs..."):
        st.session_state.language_map = get_google_languages()
        voices = get_edge_voices()
        st.session_state.voice_index = build_voice_index(voices)

language_map: Dict[str, str] = st.session_state.language_map
voice_index: VoiceIndex = st.session_state.voice_index

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

if "stt_text" not in st.session_state:
    st.session_state.stt_text = ""

language_names = sorted(language_map.keys())

mode = st.segmented_control(
    "Workflow",
    options=["Speech to Text", "Text to Speech"],
    selection_mode="single",
    default="Text to Speech",
)

if mode is None:
    mode = "Text to Speech"

source_language_name = st.selectbox("Source Language", options=["Auto Detect"] + language_names)

default_targets = ["English", "Spanish", "French", "Hindi"]
default_targets = [name for name in default_targets if name in language_map]

target_language_names = st.multiselect(
    "Target Languages (select one or many)",
    options=language_names,
    default=default_targets,
)

if mode == "Speech to Text":
    st.subheader("Speech to Text")
    left, right = st.columns([1, 1])

    with left:
        recorded_audio = st.audio_input("Record your voice")

    with right:
        uploaded_audio = st.file_uploader(
            "Or upload audio file",
            type=["wav", "flac", "aiff", "aif", "aifc"],
        )

    if st.button("Transcribe Audio", type="primary"):
        audio_bytes: bytes | None = None
        if recorded_audio is not None:
            audio_bytes = recorded_audio.getvalue()
        elif uploaded_audio is not None:
            audio_bytes = uploaded_audio.read()

        if audio_bytes is None:
            st.error("Record or upload audio first.")
        else:
            try:
                locale = speech_locale_hint(source_language_name, language_map)
                st.session_state.stt_text = transcribe_audio(audio_bytes, locale)
                st.session_state.input_text = st.session_state.stt_text
                st.success("Speech converted to text.")
            except ModuleNotFoundError:
                st.error("SpeechRecognition is not installed. Run: pip install -r requirements.txt")
            except Exception as exc:
                error_name = type(exc).__name__
                if error_name == "UnknownValueError":
                    st.error("Could not understand the audio. Try speaking clearly and recording again.")
                elif error_name == "RequestError":
                    st.error(f"Speech recognition service error: {exc}")
                else:
                    st.error(f"Audio transcription failed: {exc}")

    st.text_area(
        "Transcribed Text",
        height=180,
        key="stt_text",
        placeholder="Your speech transcription will appear here.",
    )
    st.caption("Tip: Switch to Text to Speech mode to translate and generate voice from this text.")

else:
    st.subheader("Text to Speech")
    input_text = st.text_area(
        "Input Text",
        placeholder="Type or paste text. You can also transcribe speech first, then switch to this mode.",
        height=180,
        key="input_text",
    )

    translate_and_speak = st.button("Translate + Generate Speech", type="primary")

    if translate_and_speak:
        if not input_text.strip():
            st.error("Please enter some text.")
        elif not target_language_names:
            st.error("Please select at least one target language.")
        else:
            source_code = "auto" if source_language_name == "Auto Detect" else language_map[source_language_name]
            targets = [(name, language_map[name]) for name in target_language_names]

            with st.spinner("Translating and generating speech..."):
                try:
                    outputs = run_pipeline(
                        text=input_text.strip(),
                        source_code=source_code,
                        target_codes=targets,
                        by_lang=voice_index,
                        rate=rate,
                        pitch=pitch,
                    )
                except Exception as exc:
                    st.exception(exc)
                    st.stop()

            st.success(f"Generated {len(outputs)} translated audio output(s).")

            for idx, (display_name, lang_code, translated_text, audio_bytes) in enumerate(outputs, start=1):
                with st.container(border=True):
                    st.markdown(f"### {idx}. {display_name} ({lang_code})")
                    st.write(translated_text)
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(
                        label=f"Download MP3 ({display_name})",
                        data=audio_bytes,
                        file_name=f"tts_{lang_code}_{idx}.mp3",
                        mime="audio/mpeg",
                    )

st.markdown("---")
st.caption("Note: Translation and speech recognition use online services, so internet access is required.")
