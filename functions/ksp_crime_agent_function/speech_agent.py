import json
import urllib.request
import urllib.error
import base64
import uuid
from token_manager import get_fresh_ml_token

# ============================================================
# KSP CrimeAI — Speech Agent
# Handles Speech-to-Text and Text-to-Speech via Zoho Zia
# ============================================================

CATALYST_ORG = "60072886153"

STT_URL = "https://api.catalyst.zoho.in/quickml/api/v1/models/zia/audio/transcribe"
TTS_URL = "https://api.catalyst.zoho.in/quickml/api/v1/models/zia/tts/synthesize"


def speech_to_text(audio_base64, language='en'):
    """Convert speech/audio to text using Zia STT (multipart/form-data)"""
    try:
        token = get_fresh_ml_token()
        if not token:
            return {"error": "Could not get OAuth token"}

        audio_bytes = base64.b64decode(audio_base64)

        boundary = uuid.uuid4().hex
        lang_code = {"kn": "kn", "en": "en"}.get(language, "en")

        body = b""
        body += f"--{boundary}\r\n".encode()
        body += b'Content-Disposition: form-data; name="language"\r\n\r\n'
        body += f"{lang_code}\r\n".encode()

        body += f"--{boundary}\r\n".encode()
        body += b'Content-Disposition: form-data; name="audio"; filename="audio.wav"\r\n'
        body += b"Content-Type: audio/wav\r\n\r\n"
        body += audio_bytes
        body += b"\r\n"
        body += f"--{boundary}--\r\n".encode()

        headers = {
            "CATALYST-ORG": CATALYST_ORG,
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }

        req = urllib.request.Request(STT_URL, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return {
                "text": result.get("transcript", result.get("text", "")),
                "confidence": result.get("confidence", 0),
                "language": language
            }

    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "details": e.read().decode("utf-8")}
    except Exception as e:
        return {"error": str(e)}


def text_to_speech(text, language='en', speaker=None, pitch="moderate", speed="moderate", emotion="neutral"):
    """Convert text response to speech using Zia TTS (returns audio/wav bytes)"""
    try:
        token = get_fresh_ml_token()
        if not token:
            return {"error": "Could not get OAuth token"}

        lang_code = {"kn": "kn", "en": "en"}.get(language, "en")
        default_speakers = {"en": "Mary", "kn": "Anu", "hi": "Divya"}
        voice = speaker or default_speakers.get(lang_code, "Mary")

        headers = {
            "CATALYST-ORG": CATALYST_ORG,
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json"
        }

        payload = json.dumps({
            "text": text,
            "language": lang_code,
            "speaker": voice,
            "pitch": pitch,
            "speed": speed,
            "emotion": emotion
        }).encode("utf-8")

        req = urllib.request.Request(TTS_URL, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            audio_bytes = response.read()  # audio/wav binary
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            return {
                "audio_base64": audio_b64,
                "format": "wav",
                "language": language,
                "text": text
            }

    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "details": e.read().decode("utf-8")}
    except Exception as e:
        return {"error": str(e)}


def detect_language(text):
    """Detect if text is Kannada or English"""
    kannada_chars = sum(1 for c in text if '\u0C80' <= c <= '\u0CFF')
    if kannada_chars > 0:
        return 'kn'
    return 'en'


def handle_voice_query(audio_base64, language='en'):
    """Handle complete voice query flow"""
    stt_result = speech_to_text(audio_base64, language)

    if "error" in stt_result:
        return stt_result

    text = stt_result.get("text", "")
    detected_lang = detect_language(text)

    return {
        "transcribed_text": text,
        "detected_language": detected_lang,
        "confidence": stt_result.get("confidence", 0)
    }


def handle_voice_response(text, language='en'):
    """Convert text response to voice"""
    return text_to_speech(text, language)