"""Video studio: local GUI, session Grok agent, Kie options, FFmpeg MCP edits."""

from __future__ import annotations

import json
import mimetypes
import os
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
def from_env(name: str, default: str) -> Path:
    return Path(os.environ.get(name) or default)


HARNESS = from_env("HARNESS_HOME", r"D:\harnes-code")
AUTH = from_env("GROK_OAUTH_FILE", str(Path.home() / ".dsh" / ".xai-oauth-auth.json"))
KIE_KEY = from_env("KIE_KEY_FILE", str(HARNESS / "config" / "mcp" / "kie.key"))
FFMPEG_MCP = from_env("FFMPEG_MCP", str(HARNESS / "ffmpeg-mcp-lite" / ".venv" / "Scripts" / "ffmpeg-mcp-lite.exe"))
FFMPEG = from_env("FFMPEG_PATH", str(HARNESS / "ffmpeg" / "bin" / "ffmpeg.exe"))
MEDIA = from_env("STUDIO_MEDIA", str(HARNESS / "videos"))
OUTPUT = MEDIA / "ouput"
IMAGES = MEDIA / "imagenes"
AUDIO = MEDIA / "audio"
PORT = 7474
CLIENT_ID = "b1a00492-073a-47ea-816f-4c329264a828"
PROMPT = (
    'mujer hibrida dragona, con voz angelical imponente divina, dialogo: '
    '"que es este poder puedo sentir todo el universo y mas ..." '
    "mientras las alas de dragona de energia verde se crean imponentes."
)

MODELS = {
    "grok": {
        "label": "Grok Imagine 1.5 (sesión)",
        "provider": "grok",
        "resolution": "720p",
        "qualities": ["480p", "720p", "1080p"],
        "rates": {},
        "duration": 10,
        "durations": list(range(1, 16)),
        "audio": True,
        "inputs": ["image"],
    },
    "seedance-1-pro": {
        "label": "Kie Seedance 1.0 Pro",
        "provider": "kie",
        "model": "bytedance/v1-pro-image-to-video",
        "resolution": "480p",
        "qualities": ["480p", "720p", "1080p"],
        "rates": {"480p": 2.8, "720p": 5.6, "1080p": 11.2},
        "duration": 5,
        "durations": [5, 10],
        "audio": False,
        "inputs": ["image"],
        "family": "v1",
    },
    "seedance-1-lite": {
        "label": "Kie Seedance 1.0 Lite",
        "provider": "kie",
        "model": "bytedance/v1-lite-image-to-video",
        "resolution": "480p",
        "qualities": ["480p", "720p"],
        "rates": {"480p": 1.4, "720p": 2.8},
        "duration": 5,
        "durations": [5, 10],
        "audio": False,
        "inputs": ["image"],
        "family": "v1",
    },
    "seedance-1-fast": {
        "label": "Kie Seedance 1.0 Pro Fast",
        "provider": "kie",
        "model": "bytedance/v1-pro-fast-image-to-video",
        "resolution": "720p",
        "qualities": ["720p", "1080p"],
        "rates": {"720p": 2.2, "1080p": 4.4},
        "duration": 5,
        "durations": [5, 10],
        "audio": False,
        "inputs": ["image"],
        "family": "v1",
    },
    "seedance-1-5": {
        "label": "Kie Seedance 1.5 Pro",
        "provider": "kie",
        "model": "bytedance/seedance-1.5-pro",
        "resolution": "720p",
        "qualities": ["480p", "720p", "1080p"],
        "rates": {"480p": 3.5, "720p": 7, "1080p": 14},
        "duration": 10,
        "durations": list(range(4, 13)),
        "audio": True,
        "inputs": ["image"],
        "family": "1.5",
    },
    "seedance-ref": {
        "label": "Kie Seedance 2.0 Mini · referencias",
        "provider": "kie",
        "model": "bytedance/seedance-2-mini",
        "resolution": "720p",
        "qualities": ["480p", "720p"],
        "rates": {"480p": 4.1, "720p": 8.2},
        "duration": 5,
        "durations": list(range(4, 16)),
        "audio": True,
        "reference": True,
        "inputs": ["scene", "characters", "audio"],
        "family": "mini",
    },
    "seedance-2-fast": {
        "label": "Kie Seedance 2.0 Fast",
        "provider": "kie",
        "model": "bytedance/seedance-2-fast",
        "resolution": "720p",
        "qualities": ["480p", "720p"],
        "rates": {"480p": 3, "720p": 6},
        "duration": 5,
        "durations": list(range(4, 16)),
        "audio": True,
        "inputs": ["image"],
        "family": "mini",
    },
    "seedance-2": {
        "label": "Kie Seedance 2.0",
        "provider": "kie",
        "model": "bytedance/seedance-2",
        "resolution": "720p",
        "qualities": ["480p", "720p", "1080p"],
        "rates": {"480p": 6, "720p": 12, "1080p": 24},
        "duration": 5,
        "durations": list(range(4, 16)),
        "audio": True,
        "inputs": ["image"],
        "family": "mini",
    },
    "seedance-2-5-draft": {
        "label": "Kie Seedance 2.5 Draft",
        "provider": "kie",
        "model": "bytedance/seedance-2-5-draft",
        "resolution": "720p",
        "qualities": ["720p"],
        "rates": {"720p": 8},
        "duration": 5,
        "durations": list(range(4, 13)),
        "audio": True,
        "inputs": ["image"],
        "family": "mini",
    },
    "seedance-2-mini": {
        "label": "Kie Seedance 2.0 Mini",
        "provider": "kie",
        "model": "bytedance/seedance-2-mini",
        "resolution": "720p",
        "qualities": ["480p", "720p"],
        "rates": {"480p": 4.1, "720p": 8.2},
        "duration": 10,
        "durations": list(range(4, 16)),
        "audio": True,
        "inputs": ["image"],
        "family": "mini",
    },
}


IMAGE_MODELS = {
    "grok": {"label": "Grok Imagine 2.0 (sesión)", "provider": "grok", "qualities": ["1k", "2k"], "rates": {}},
    "seedream-3": {"label": "Seedream 3", "provider": "kie", "qualities": ["1K"], "rates": {"1K": 2}},
    "seedream-4": {"label": "Seedream 4", "provider": "kie", "qualities": ["1K", "2K"], "rates": {"1K": 3, "2K": 6}},
    "seedream-4-5": {"label": "Seedream 4.5", "provider": "kie", "qualities": ["1K", "2K"], "rates": {"1K": 4, "2K": 8}},
    "seedream-5-lite": {"label": "Seedream 5 Lite", "provider": "kie", "qualities": ["1K", "2K"], "rates": {"1K": 3, "2K": 6}},
    "seedream-5": {"label": "Seedream 5 Flash", "provider": "kie", "qualities": ["1K", "2K"], "rates": {"1K": 2, "2K": 5}},
    "seedream-4-edit": {"label": "Seedream 4 edición", "provider": "kie", "qualities": ["1K", "2K"], "rates": {"1K": 3, "2K": 6}},
    "seedream-4-5-edit": {"label": "Seedream 4.5 edición", "provider": "kie", "qualities": ["1K", "2K"], "rates": {"1K": 4, "2K": 8}},
    "seedream-5-lite-edit": {"label": "Seedream 5 Lite edición", "provider": "kie", "qualities": ["1K", "2K"], "rates": {"1K": 3, "2K": 6}},
    "seedream-5-edit": {"label": "Seedream 5 Flash edición", "provider": "kie", "qualities": ["1K", "2K"], "rates": {"1K": 2, "2K": 5}},
}
GEMINI_VOICES = [
    {"id": "Fola", "label": "Fola"},
    {"id": "Zephyr", "label": "Zephyr"},
    {"id": "Kore", "label": "Kore"},
    {"id": "Puck", "label": "Puck"},
    {"id": "Charon", "label": "Charon"},
    {"id": "Aoede", "label": "Aoede"},
    {"id": "Fenrir", "label": "Fenrir"},
    {"id": "Leda", "label": "Leda"},
    {"id": "Orus", "label": "Orus"},
    {"id": "Enceladus", "label": "Enceladus"},
]
ELEVEN_VOICES = [
    {"id": "EkK5I93UQWFDigLMpZcX", "label": "James", "demo": "https://static.aiquickdraw.com/elevenlabs/voice/EkK5I93UQWFDigLMpZcX.mp3"},
    {"id": "N2lVS1w4EtoT3dr4eOWO", "label": "Callum", "demo": "https://static.aiquickdraw.com/elevenlabs/voice/N2lVS1w4EtoT3dr4eOWO.mp3"},
    {"id": "FGY2WhTYpPnrIDTdsKH5", "label": "Laura", "demo": "https://static.aiquickdraw.com/elevenlabs/voice/FGY2WhTYpPnrIDTdsKH5.mp3"},
    {"id": "nPczCjzI2devNBz1zQrb", "label": "Brian", "demo": "https://static.aiquickdraw.com/elevenlabs/voice/nPczCjzI2devNBz1zQrb.mp3"},
    {"id": "hpp4J3VqNfWAUOO0d1Us", "label": "Bella", "demo": "https://static.aiquickdraw.com/elevenlabs/voice/hpp4J3VqNfWAUOO0d1Us.mp3"},
    {"id": "TX3LPaxmHKxFdv7VOQHJ", "label": "Liam", "demo": "https://static.aiquickdraw.com/elevenlabs/voice/TX3LPaxmHKxFdv7VOQHJ.mp3"},
    {"id": "UgBBYS2sOqTuMpoF3BR0", "label": "Mark", "demo": "https://static.aiquickdraw.com/elevenlabs/voice/UgBBYS2sOqTuMpoF3BR0.mp3"},
    {"id": "1SM7GgM6IMuvQlz2BwM3", "label": "Mark casual", "demo": "https://static.aiquickdraw.com/elevenlabs/voice/1SM7GgM6IMuvQlz2BwM3.mp3"},
]
GROK_VOICES = [
    {"id": "altair", "label": "Altair", "demo": "session"},
    {"id": "ara", "label": "Ara", "demo": "session"},
    {"id": "atlas", "label": "Atlas", "demo": "session"},
    {"id": "aurora", "label": "Aurora", "demo": "session"},
    {"id": "carina", "label": "Carina", "demo": "session"},
    {"id": "castor", "label": "Castor", "demo": "session"},
    {"id": "celeste", "label": "Celeste", "demo": "session"},
    {"id": "cosmo", "label": "Cosmo", "demo": "session"},
    {"id": "eve", "label": "Eve", "demo": "session"},
    {"id": "helios", "label": "Helios", "demo": "session"},
    {"id": "helix", "label": "Helix", "demo": "session"},
    {"id": "iris", "label": "Iris", "demo": "session"},
    {"id": "kepler", "label": "Kepler", "demo": "session"},
    {"id": "leo", "label": "Leo", "demo": "session"},
    {"id": "liora", "label": "Liora", "demo": "session"},
    {"id": "lumen", "label": "Lumen", "demo": "session"},
    {"id": "luna", "label": "Luna", "demo": "session"},
    {"id": "lux", "label": "Lux", "demo": "session"},
    {"id": "naksh", "label": "Naksh", "demo": "session"},
    {"id": "orion", "label": "Orion", "demo": "session"},
    {"id": "perseus", "label": "Perseus", "demo": "session"},
    {"id": "rex", "label": "Rex", "demo": "session"},
    {"id": "rigel", "label": "Rigel", "demo": "session"},
    {"id": "sal", "label": "Sal", "demo": "session"},
    {"id": "sirius", "label": "Sirius", "demo": "session"},
    {"id": "ursa", "label": "Ursa", "demo": "session"},
    {"id": "zagan", "label": "Zagan", "demo": "session"},
    {"id": "zenith", "label": "Zenith", "demo": "session"},
]
AUDIO_MODELS = {
    "grok": {"label": "Grok texto a voz (sesión)", "provider": "grok", "qualities": [], "voices": GROK_VOICES},
    "google/gemini-3-8-flash-lite-tts": {"label": "Gemini 3.8 Flash Lite", "provider": "kie", "qualities": [], "per_1k": 1, "voices": GEMINI_VOICES},
    "google/gemini-3-8-flash-tts": {"label": "Gemini 3.8 Flash", "provider": "kie", "qualities": [], "per_1k": 2, "voices": GEMINI_VOICES},
    "google/gemini-3-1-flash-tts": {"label": "Gemini 3.1 Flash", "provider": "kie", "qualities": [], "per_1k": 3},
    "elevenlabs/text-to-speech-turbo-2-5": {"label": "ElevenLabs Turbo 2.5", "provider": "kie", "qualities": [], "per_1k": 8, "voices": ELEVEN_VOICES},
    "elevenlabs/text-to-speech-multilingual-v2": {"label": "ElevenLabs Multilingual V2", "provider": "kie", "qualities": [], "per_1k": 12, "voices": ELEVEN_VOICES},
}


def kie_key() -> str:
    key = os.environ.get("KIE_API_KEY", "").strip()
    if not key and KIE_KEY.is_file():
        key = KIE_KEY.read_text(encoding="utf-8").strip()
    if not key:
        raise RuntimeError(f"Falta la key de Kie en {KIE_KEY}")
    return key


def grok_token() -> str:
    direct = (os.environ.get("XAI_API_KEY") or os.environ.get("GROK_TOKEN") or "").strip()
    if direct:
        return direct
    auth = json.loads(AUTH.read_text(encoding="utf-8"))
    credential = auth["credential"]
    if credential.get("expires", 0) < time.time() * 1000 + 60_000:
        body = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": credential["refresh"],
        }).encode()
        req = urllib.request.Request(
            "https://auth.x.ai/oauth2/token",
            data=body,
            headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=40) as response:
            refreshed = json.loads(response.read().decode())
        credential["access"] = refreshed["access_token"]
        if refreshed.get("refresh_token"):
            credential["refresh"] = refreshed["refresh_token"]
        expires_in = refreshed.get("expires_in") or 3600
        credential["expires"] = int(time.time() * 1000 + expires_in * 1000 - 5 * 60 * 1000)
        AUTH.write_text(json.dumps(auth, indent=2) + "\n", encoding="utf-8")
    return credential["access"]


def http_json(method: str, url: str, payload: dict | None = None, headers: dict | None = None, timeout: int = 120) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {error.code}: {detail}") from error


def save_url(url: str, name: str, folder: Path = OUTPUT) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    headers = {"User-Agent": "video-studio"}
    if "x.ai" in url or "vidgen" in url:
        headers["Authorization"] = f"Bearer {grok_token()}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            target.write_bytes(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"No se pudo descargar el resultado ({error.code}): {detail or error.reason}") from error
    return str(target)


def save_image_result(url: str, name: str) -> str:
    return save_url(url, name, IMAGES)


def upload_kie(image: Path) -> str:
    boundary = uuid.uuid4().hex
    file_bytes = image.read_bytes()
    chunks = [
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"uploadPath\"\r\n\r\nimages/user-uploads\r\n".encode(),
        (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{image.name}\"\r\n"
            f"Content-Type: {mimetypes.guess_type(image.name)[0] or 'application/octet-stream'}\r\n\r\n"
        ).encode() + file_bytes + b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    req = urllib.request.Request(
        "https://kieai.redpandaai.co/api/file-stream-upload",
        data=b"".join(chunks),
        method="POST",
        headers={
            "Authorization": f"Bearer {kie_key()}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        body = json.loads(response.read().decode())
    if body.get("code") != 200:
        raise RuntimeError(body.get("msg") or "upload failed")
    return body["data"]["downloadUrl"]


def kie_wait(task_id: str) -> dict:
    headers = {"Authorization": f"Bearer {kie_key()}", "Accept": "application/json"}
    deadline = time.time() + 16 * 60
    while time.time() < deadline:
        info = http_json("GET", f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}", headers=headers)
        data = info.get("data") or {}
        state = data.get("state")
        if state == "success":
            return data
        if state == "fail":
            raise RuntimeError(f"{data.get('failCode')} {data.get('failMsg')}".strip())
        time.sleep(8)
    raise TimeoutError(task_id)


def generate(model_id: str, prompt: str, image: Path | None, duration: int | None = None, aspect: str = "16:9", characters: list | None = None, resolution: str | None = None) -> dict:
    if model_id == "seedance-ref":
        return make_reference("seedance-ref", prompt, aspect, duration, characters or [], str(image) if image else "", resolution)
    spec = MODELS[model_id]
    quality = resolution if resolution in spec.get("qualities", []) else spec["resolution"]
    stamp = time.strftime("%H%M%S")
    if spec["provider"] == "grok":
        if image is None:
            raise RuntimeError("Grok image-to-video necesita una imagen")
        import base64
        mime = mimetypes.guess_type(image.name)[0] or "image/png"
        data_url = "data:" + mime + ";base64," + base64.b64encode(image.read_bytes()).decode()
        seconds = int(duration or spec["duration"])
        started = http_json(
            "POST",
            "https://api.x.ai/v1/videos/generations",
            {
                "model": "grok-imagine-video-1.5",
                "prompt": prompt,
                "duration": seconds,
                "aspect_ratio": aspect or "16:9",
                "resolution": quality,
                "image": {"url": data_url},
            },
            headers={"Authorization": f"Bearer {grok_token()}", "Content-Type": "application/json"},
            timeout=180,
        )
        request_id = started["request_id"]
        deadline = time.time() + 16 * 60
        result = {}
        while time.time() < deadline:
            time.sleep(8)
            result = http_json(
                "GET",
                f"https://api.x.ai/v1/videos/{request_id}",
                headers={"Authorization": f"Bearer {grok_token()}"},
            )
            if result.get("status") in {"done", "failed"}:
                break
        if result.get("status") != "done":
            raise RuntimeError(json.dumps(result.get("error") or result)[:400])
        path = save_url(result["video"]["url"], f"grok-{stamp}.mp4")
        ticks = (result.get("usage") or {}).get("cost_in_usd_ticks")
        return {"file": path, "model": model_id, "usd": None if ticks is None else ticks / 10_000_000_000, "folder": str(OUTPUT)}
    if image is None:
        raise RuntimeError("Estos modelos de Kie se usan aquí con imagen")
    image_url = upload_kie(image)
    seconds = int(duration or spec["duration"])
    headers = {
        "Authorization": f"Bearer {kie_key()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if spec.get("family") == "v1":
        payload = {
            "model": spec["model"],
            "input": {
                "prompt": prompt,
                "image_url": image_url,
                "resolution": quality,
                "duration": "5" if seconds < 8 else "10",
                "camera_fixed": False,
                "seed": -1,
                "enable_safety_checker": True,
                "nsfw_checker": False,
            },
        }
    elif model_id == "seedance-1-5":
        payload = {
            "model": spec["model"],
            "input": {
                "prompt": prompt,
                "input_urls": [image_url],
                "aspect_ratio": aspect or "16:9",
                "resolution": quality,
                "duration": max(4, min(12, seconds)),
                "fixed_lens": False,
                "generate_audio": True,
                "nsfw_checker": False,
            },
        }
    else:
        payload = {
            "model": spec["model"],
            "input": {
                "prompt": prompt,
                "first_frame_url": image_url,
                "generate_audio": True,
                "resolution": quality,
                "aspect_ratio": aspect or "16:9",
                "duration": max(4, min(15, seconds)),
                "nsfw_checker": False,
            },
        }
    created = http_json("POST", "https://api.kie.ai/api/v1/jobs/createTask", payload, headers=headers)
    if created.get("code") != 200:
        raise RuntimeError(created.get("msg") or "kie create failed")
    done = kie_wait(created["data"]["taskId"])
    result = json.loads(done["resultJson"])
    path = save_url(result["resultUrls"][0], f"{model_id}-{stamp}.mp4")
    credits = done.get("creditsConsumed") or 0
    return {"file": path, "model": model_id, "credits": credits, "usd": credits * 0.005, "folder": str(OUTPUT)}


def kie_task(payload: dict) -> tuple[dict, str]:
    headers = {
        "Authorization": f"Bearer {kie_key()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    created = http_json("POST", "https://api.kie.ai/api/v1/jobs/createTask", payload, headers=headers)
    if created.get("code") != 200:
        raise RuntimeError(created.get("msg") or "kie create failed")
    done = kie_wait(created["data"]["taskId"])
    result = json.loads(done["resultJson"])
    return done, result["resultUrls"][0]


def grok_tts(text: str, voice: str, language: str = "es-MX") -> bytes:
    data = json.dumps({"text": text, "voice_id": voice or "eve", "language": language}).encode()
    req = urllib.request.Request(
        "https://api.x.ai/v1/tts",
        data=data,
        method="POST",
        headers={"Authorization": f"Bearer {grok_token()}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"HTTP {error.code}: {detail}") from error


def grok_voice_demo(voice: str) -> Path:
    AUDIO.mkdir(parents=True, exist_ok=True)
    target = AUDIO / f"demo-{voice}.mp3"
    if target.is_file() and target.stat().st_size > 1000:
        return target
    target.write_bytes(grok_tts("Hola. Esta es una muestra corta de mi voz.", voice))
    return target


def make_audio(model_id: str, prompt: str, seconds: int | None, voice: str = "") -> dict:
    if model_id == "grok":
        AUDIO.mkdir(parents=True, exist_ok=True)
        path = AUDIO / f"grok-{time.strftime('%H%M%S')}.mp3"
        path.write_bytes(grok_tts(prompt, voice or "eve"))
        return {"file": str(path), "model": "grok", "folder": str(AUDIO), "provider": "grok"}
    style = f"Duración aproximada: {seconds} segundos." if seconds else ""
    if model_id.startswith("google/"):
        speaker = {"speaker_id": "Speaker 1"}
        if voice:
            speaker["voice_name"] = voice
        payload = {
            "model": model_id,
            "input": {
                "speakers": [speaker],
                "dialogue_turns": [{"speaker_id": "Speaker 1", "text": prompt, "style": style or "Natural dialogue"}],
            },
        }
    else:
        payload = {"model": model_id, "input": {"text": prompt, "voice": voice or "EkK5I93UQWFDigLMpZcX"}}
    done, url = kie_task(payload)
    suffix = Path(urllib.parse.urlparse(url).path).suffix or ".wav"
    path = save_url(url, f"dialogo-{time.strftime('%H%M%S')}{suffix}", AUDIO)
    credits = done.get("creditsConsumed") or 0
    return {"file": path, "model": model_id, "credits": credits, "usd": credits * 0.005, "folder": str(AUDIO)}


def make_reference(model_id: str, prompt: str, aspect: str, duration: int | None, characters: list[dict], scene_image: str, resolution: str | None = None) -> dict:
    images = []
    audios = []
    named = []
    for item in characters:
        image = item.get("image") or ""
        audio = item.get("audio") or ""
        image_url = upload_kie(Path(image)) if image else ""
        audio_url = upload_kie(Path(audio)) if audio else ""
        if image_url:
            images.append(image_url)
        if audio_url:
            audios.append(audio_url)
        if image_url:
            named.append({"name": item.get("name") or f"personaje{len(named) + 1}", "image": image_url, "audio": audio_url})
    if scene_image:
        images.insert(0, upload_kie(Path(scene_image)))
    if not images:
        raise RuntimeError("Agrega al menos una imagen de personaje o de escena")
    seconds = int(duration or 5)
    aspect = aspect or "16:9"
    if model_id == "seedance-ref":
        payload = {
            "model": "bytedance/seedance-2-mini",
            "input": {
                "prompt": prompt,
                "reference_image_urls": images[:9],
                "reference_audio_urls": audios[:3],
                "generate_audio": True,
                "resolution": resolution or "720p",
                "aspect_ratio": aspect,
                "duration": max(4, min(15, seconds)),
                "nsfw_checker": False,
            },
        }
    elif model_id == "wan-r2v":
        payload = {
            "model": "wan/2-7-r2v",
            "input": {
                "prompt": prompt,
                "reference_image": images[:5],
                "resolution": "720p",
                "aspect_ratio": aspect if aspect in {"16:9", "9:16", "1:1", "4:3", "3:4"} else "16:9",
                "duration": max(2, min(10, seconds)),
                "prompt_extend": False,
                "watermark": False,
                "nsfw_checker": False,
                **({"reference_voice": audios[0]} if audios else {}),
            },
        }
    elif model_id == "kling-omni":
        payload = {
            "model": "kling-3.0-omni/reference-to-video",
            "input": {
                "prompt": prompt,
                "image_urls": images[:4],
                "duration": max(3, min(15, seconds)),
                "resolution": "720p",
                "aspect_ratio": aspect if aspect in {"16:9", "9:16", "1:1"} else "16:9",
                "audio": True,
                "elements": [
                    {
                        "name": item["name"].replace(" ", "_"),
                        "description": item["name"],
                        "element_input_urls": [item["image"]],
                        **({"element_input_audio_urls": [item["audio"]]} if item["audio"] else {}),
                    }
                    for item in named[:3]
                ],
            },
        }
    elif model_id == "happyhorse":
        payload = {
            "model": "happyhorse/reference-to-video",
            "input": {
                "prompt": prompt,
                "reference_image": images[:9],
                "resolution": "720p",
                "aspect_ratio": aspect if aspect in {"16:9", "9:16", "1:1", "4:3", "3:4"} else "16:9",
                "duration": max(3, min(15, seconds)),
            },
        }
    else:
        payload = {
            "model": "happyhorse-1-1/reference-to-video",
            "input": {
                "prompt": prompt,
                "reference_image": images[:9],
                "resolution": "720p",
                "aspect_ratio": aspect if aspect in {"16:9", "9:16", "1:1", "4:3", "3:4"} else "16:9",
                "duration": max(3, min(15, seconds)),
            },
        }
    done, url = kie_task(payload)
    path = save_url(url, f"ref-{model_id}-{time.strftime('%H%M%S')}.mp4")
    credits = done.get("creditsConsumed") or 0
    return {"file": path, "model": model_id, "credits": credits, "usd": credits * 0.005, "folder": str(OUTPUT)}


def last_frame(video: Path) -> Path:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / f"{video.stem}-ultimo.png"
    proc = subprocess.run(
        [str(FFMPEG), "-y", "-sseof", "-0.08", "-i", str(video), "-frames:v", "1", str(target)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not target.is_file():
        raise RuntimeError(proc.stderr[-400:] or "no se pudo sacar el último fotograma")
    return target


def extend_grok(video: Path, prompt: str, duration: int = 6) -> dict:
    import base64
    seconds = max(2, min(10, int(duration or 6)))
    source = video
    prefix = None
    probe = subprocess.run(
        [str(FFMPEG.with_name("ffprobe.exe")), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        capture_output=True,
        text=True,
    )
    try:
        length = float(probe.stdout.strip() or "0")
    except ValueError:
        length = 0
    if length > 15:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        prefix = OUTPUT / f"{video.stem}-prefijo.mp4"
        source = OUTPUT / f"{video.stem}-cola15.mp4"
        subprocess.run([str(FFMPEG), "-y", "-ss", str(max(0, length - 15)), "-i", str(video), "-c", "copy", str(source)], check=True)
        subprocess.run([str(FFMPEG), "-y", "-t", str(max(0, length - 15)), "-i", str(video), "-c", "copy", str(prefix)], check=True)
    data_url = "data:video/mp4;base64," + base64.b64encode(source.read_bytes()).decode()
    started = http_json(
        "POST",
        "https://api.x.ai/v1/videos/extensions",
        {
            "model": "grok-imagine-video",
            "prompt": prompt,
            "duration": seconds,
            "video": {"url": data_url},
        },
        headers={"Authorization": f"Bearer {grok_token()}", "Content-Type": "application/json"},
        timeout=180,
    )
    request_id = started["request_id"]
    deadline = time.time() + 16 * 60
    result: dict = {}
    while time.time() < deadline:
        time.sleep(8)
        result = http_json(
            "GET",
            f"https://api.x.ai/v1/videos/{request_id}",
            headers={"Authorization": f"Bearer {grok_token()}"},
        )
        if result.get("status") in {"done", "failed"}:
            break
    if result.get("status") != "done":
        raise RuntimeError(json.dumps(result.get("error") or result)[:400])
    path = save_url(result["video"]["url"], f"grok-extend-{time.strftime('%H%M%S')}.mp4")
    if prefix is not None and prefix.is_file():
        joined = OUTPUT / f"grok-extend-full-{time.strftime('%H%M%S')}.mp4"
        listing = OUTPUT / f"concat-{time.strftime('%H%M%S')}.txt"
        listing.write_text(f"file '{prefix.as_posix()}'\nfile '{Path(path).as_posix()}'\n", encoding="utf-8")
        subprocess.run([str(FFMPEG), "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(joined)], check=True)
        path = str(joined)
    ticks = (result.get("usage") or {}).get("cost_in_usd_ticks")
    return {"file": path, "model": "grok-extend", "usd": None if ticks is None else ticks / 10_000_000_000, "folder": str(OUTPUT)}


def make_image(model_id: str, prompt: str, image: Path | None, aspect: str = "16:9", resolution: str = "1K") -> dict:
    stamp = time.strftime("%H%M%S")
    if model_id == "grok":
        import base64
        headers = {"Authorization": f"Bearer {grok_token()}", "Content-Type": "application/json"}
        if image is None:
            body = http_json(
                "POST",
                "https://api.x.ai/v1/images/generations",
                {
                    "model": "grok-imagine-image-2.0",
                    "prompt": prompt,
                    "aspect_ratio": aspect,
                    "n": 1,
                    "response_format": "b64_json",
                },
                headers=headers,
            )
        else:
            mime = mimetypes.guess_type(image.name)[0] or "image/png"
            data_url = "data:" + mime + ";base64," + base64.b64encode(image.read_bytes()).decode()
            body = http_json(
                "POST",
                "https://api.x.ai/v1/images/edits",
                {
                    "model": "grok-imagine-image-2.0",
                    "prompt": prompt,
                    "response_format": "b64_json",
                    "image": {"url": data_url, "type": "image_url"},
                },
                headers=headers,
            )
        item = (body.get("data") or [{}])[0]
        IMAGES.mkdir(parents=True, exist_ok=True)
        path = IMAGES / f"grok-{stamp}.png"
        if item.get("b64_json"):
            import base64 as b64
            path.write_bytes(b64.b64decode(item["b64_json"]))
        elif item.get("url"):
            path = Path(save_image_result(item["url"], path.name))
        else:
            raise RuntimeError("Grok no devolvió una imagen")
        ticks = (body.get("usage") or {}).get("cost_in_usd_ticks")
        return {"file": str(path), "model": "grok", "folder": str(IMAGES), "usd": None if ticks is None else ticks / 10_000_000_000, "provider": "grok"}
    image_url = upload_kie(image) if image else None
    headers = {
        "Authorization": f"Bearer {kie_key()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if model_id == "seedream-4":
        if image_url:
            payload = {
                "model": "bytedance/seedream-v4-edit",
                "input": {
                    "prompt": prompt,
                    "image_urls": [image_url],
                    "image_size": "landscape_16_9" if aspect == "16:9" else "square_hd",
                    "image_resolution": "1K",
                    "max_images": 1,
                    "nsfw_checker": False,
                },
            }
        else:
            payload = {
                "model": "bytedance/seedream-v4-text-to-image",
                "input": {
                    "prompt": prompt,
                    "image_size": "landscape_16_9" if aspect == "16:9" else "square_hd",
                    "image_resolution": "1K",
                    "max_images": 1,
                    "nsfw_checker": False,
                },
            }
    else:
        common = {
            "prompt": prompt,
            "aspect_ratio": aspect if aspect in {"1:1", "4:3", "3:4", "16:9", "9:16", "2:3", "3:2", "21:9"} else "16:9",
            "size": "1K",
            "output_format": "png",
            "nsfw_checker": False,
        }
        if image_url:
            payload = {"model": "seedream/5-flash-image-to-image", "input": {**common, "image_urls": [image_url]}}
        else:
            payload = {"model": "seedream/5-flash-text-to-image", "input": common}
    created = http_json("POST", "https://api.kie.ai/api/v1/jobs/createTask", payload, headers=headers)
    if created.get("code") != 200:
        raise RuntimeError(created.get("msg") or "kie image failed")
    done = kie_wait(created["data"]["taskId"])
    result = json.loads(done["resultJson"])
    path = save_image_result(result["resultUrls"][0], f"{model_id}-{stamp}.png")
    credits = done.get("creditsConsumed") or 0
    return {"file": path, "model": model_id, "credits": credits, "usd": credits * 0.005, "folder": str(IMAGES)}


CHAT_MODELS = [
    "grok-4.3",
    "grok-4.5",
    "grok-4.6",
    "grok-4.7",
    "grok-4.20-0309-reasoning",
    "grok-4.20-0309-non-reasoning",
    "grok-4.20-multi-agent-0309",
    "grok-build-0.1",
]


def chat_text(model: str, system: str, user: str) -> str:
    chosen = model if model in CHAT_MODELS else "grok-4.3"
    body = http_json(
        "POST",
        "https://api.x.ai/v1/chat/completions",
        {"model": chosen, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        headers={"Authorization": f"Bearer {grok_token()}", "Content-Type": "application/json"},
        timeout=120,
    )
    return body["choices"][0]["message"]["content"].strip()


def improve_prompt(model: str, prompt: str, kind: str) -> str:
    systems = {
        "video": (
            "Mejora un prompt de video. Deja acción visible, cámara, luz, continuidad y diálogo entre comillas si hay voz. "
            "No inventes un final distinto. Devuelve solo el prompt mejorado."
        ),
        "image": (
            "Mejora un prompt de imagen, para crear o editar. Deja sujeto, estilo, luz, composición y qué debe conservarse si es una edición. "
            "Devuelve solo el prompt mejorado."
        ),
        "idea": (
            "Mejora una idea de video para partirla después en escenas. Hazla más visual y continua, sin cambiar el objetivo. "
            "Devuelve solo la idea mejorada."
        ),
        "audio": (
            "Mejora un diálogo para texto a voz. Deja las frases habladas, quién habla y el tono. "
            "No agregues cámara ni planos. Devuelve solo el diálogo mejorado."
        ),
    }
    return chat_text(model, systems.get(kind) or systems["video"], prompt)


def plan_scenes(idea: str, count: int, model: str = "grok-4.3") -> list[dict]:
    count = max(1, min(8, int(count)))
    body = http_json(
        "POST",
        "https://api.x.ai/v1/chat/completions",
        {
            "model": model if model in CHAT_MODELS else "grok-4.3",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Divide una idea de video en escenas. Optimiza cada prompt para un modelo de video: "
                        "acción visible, cámara, luz, diálogo entre comillas si hay voz, continuidad con la escena anterior. "
                        "Responde solo JSON: {\"scenes\":[{\"title\":\"\",\"prompt\":\"\"}]}. "
                        f"Exactamente {count} escenas."
                    ),
                },
                {"role": "user", "content": idea},
            ],
        },
        headers={"Authorization": f"Bearer {grok_token()}", "Content-Type": "application/json"},
        timeout=120,
    )
    text = body["choices"][0]["message"]["content"]
    start = text.find("{")
    end = text.rfind("}")
    parsed = json.loads(text[start:end + 1])
    scenes = parsed.get("scenes") or []
    return scenes[:count]


def run_scenes(scenes: list[dict], default_image: str, base_video: str = "") -> list[dict]:
    results = []
    previous: Path | None = Path(base_video) if base_video else None
    for index, scene in enumerate(scenes):
        model = scene.get("model") or "grok"
        prompt = scene.get("prompt") or ""
        mode = scene.get("mode") or ("image" if index == 0 else "last_frame")
        duration = scene.get("duration") or None
        if mode == "extend":
            if previous is None:
                raise RuntimeError("La extensión nativa necesita el video de la escena anterior")
            if model != "grok":
                raise RuntimeError("La extensión nativa solo existe en Grok")
            item = extend_grok(previous, prompt, int(duration or 6))
        else:
            if mode == "last_frame":
                if previous is None:
                    raise RuntimeError("No hay video anterior para sacar el fotograma")
                image = last_frame(previous)
            else:
                image = Path(scene.get("image_path") or default_image)
            item = generate(model, prompt, image, int(duration) if duration else None, scene.get("aspect") or "16:9", scene.get("characters") or [], scene.get("resolution"))
        item["scene"] = index + 1
        item["mode"] = mode
        results.append(item)
        previous = Path(item["file"])
    return results


def ffmpeg_mcp(tool: str, arguments: dict) -> str:
    if not FFMPEG_MCP.is_file():
        raise RuntimeError(f"No está el editor MCP: {FFMPEG_MCP}")
    env = os.environ.copy()
    env["FFMPEG_PATH"] = str(FFMPEG)
    env["FFPROBE_PATH"] = str(FFMPEG.with_name("ffprobe.exe"))
    env["FFMPEG_OUTPUT_DIR"] = str(OUTPUT)
    proc = subprocess.Popen(
        [str(FFMPEG_MCP)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        env=env,
    )
    assert proc.stdin and proc.stdout

    def send(message: dict) -> dict:
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError("el editor MCP cerró la conexión")
        return json.loads(line)

    try:
        send({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "video-studio", "version": "0.1.0"},
            },
        })
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        proc.stdin.flush()
        result = send({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        })
        if "error" in result:
            raise RuntimeError(str(result["error"]))
        content = result.get("result", {}).get("content") or []
        texts = [item.get("text", "") for item in content if isinstance(item, dict)]
        return "\n".join(texts) or json.dumps(result.get("result"))
    finally:
        proc.kill()


def grok_chat(messages: list[dict]) -> dict:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "generate_video",
                "description": "Genera un video. model: grok, seedance-1-pro, seedance-1-5 o seedance-2-mini.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "prompt": {"type": "string"},
                        "image_path": {"type": "string"},
                        "duration": {"type": "integer"},
                    },
                    "required": ["model", "prompt"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "edit_video",
                "description": "Recorta un video usando el MCP editor FFmpeg. start y end en segundos o HH:MM:SS.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    },
                    "required": ["file_path", "start_time", "end_time"],
                },
            },
        },
    ]
    transcript = [{
        "role": "system",
        "content": (
            "Eres el agente del estudio de video. Grok Imagine 1.5 es el modelo por defecto. "
            "Kie solo si el usuario lo pide: seedance-1-pro, seedance-1-5, seedance-2-mini. "
            "Para recortar usa edit_video, que llama al MCP de FFmpeg. Responde en español."
        ),
    }, *messages]
    video = None
    for _ in range(4):
        body = http_json(
            "POST",
            "https://api.x.ai/v1/chat/completions",
            {"model": "grok-4.7", "messages": transcript, "tools": tools, "tool_choice": "auto"},
            headers={"Authorization": f"Bearer {grok_token()}", "Content-Type": "application/json"},
            timeout=120,
        )
        message = body["choices"][0]["message"]
        transcript.append(message)
        calls = message.get("tool_calls") or []
        if not calls:
            return {"reply": message.get("content") or "", "video": video}
        for call in calls:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"] or "{}")
            try:
                if name == "generate_video":
                    image = Path(args["image_path"]) if args.get("image_path") else None
                    video = generate(args.get("model") or "grok", args["prompt"], image, args.get("duration"))
                    text = json.dumps(video)
                elif name == "edit_video":
                    text = ffmpeg_mcp("ffmpeg_trim", {
                        "file_path": args["file_path"],
                        "start_time": args["start_time"],
                        "end_time": args["end_time"],
                    })
                else:
                    text = "herramienta desconocida"
            except Exception as error:
                text = f"error: {error}"
            transcript.append({"role": "tool", "tool_call_id": call["id"], "content": text})
    return {"reply": "No pude cerrar la tarea en este turno.", "video": video}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def send_json(self, payload: dict, status: int = 200) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/jobs":
            self.send_json({"jobs": job_snapshot(), "billing": billing()})
            return
        if path == "/api/models":
            self.send_json({
                "models": MODELS,
                "images": IMAGE_MODELS,
                "audios": AUDIO_MODELS,
                "chat_models": CHAT_MODELS,
                "chat_default": "grok-4.3",
                "prompt": PROMPT,
                "output": str(OUTPUT),
            })
            return
        if path == "/api/videos":
            files = []
            if OUTPUT.is_dir():
                files = [item.name for item in sorted(OUTPUT.glob("*.mp4"), key=lambda item: item.stat().st_mtime, reverse=True)[:20]]
            self.send_json({"files": files})
            return
        if path == "/api/voice-demo":
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            voice = (query.get("voice") or ["eve"])[0]
            if voice not in {item["id"] for item in GROK_VOICES}:
                self.send_error(404)
                return
            data = grok_voice_demo(voice).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path.startswith("/api/thumb"):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            raw_path = (query.get("path") or [""])[0]
            target = Path(raw_path).resolve()
            allowed = str(target).lower().startswith(("d:\\", "c:\\users\\eon\\"))
            if not allowed or not target.is_file() or target.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                self.send_error(404)
                return
            data = target.read_bytes()
            mime = mimetypes.guess_type(target.name)[0] or "image/png"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path.startswith("/media/"):
            name = Path(urllib.parse.unquote(path[7:])).name
            target = None
            for folder in (OUTPUT, IMAGES, AUDIO):
                candidate = (folder / name).resolve()
                if str(candidate).startswith(str(folder.resolve())) and candidate.is_file():
                    target = candidate
                    break
            if target is None:
                self.send_error(404)
                return
            data = target.read_bytes()
            mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        page = (STATIC / "index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        path = urllib.parse.urlparse(self.path).path
        try:
            if path == "/api/chat":
                body = json.loads(raw.decode())
                self.send_json(grok_chat(body.get("messages") or []))
                return
            if path == "/api/open":
                body = json.loads(raw.decode() or "{}")
                open_folder(body.get("path") or "")
                self.send_json({"ok": True})
                return
            if path == "/api/pick":
                body = json.loads(raw.decode() or "{}")
                chosen = pick_path(body.get("kind") or "image")
                self.send_json({"file": chosen})
                return
            if path == "/api/improve":
                body = json.loads(raw.decode())
                self.send_json({"prompt": improve_prompt(body.get("model") or "grok-4.3", body.get("prompt") or "", body.get("kind") or "video")})
                return
            if path == "/api/plan":
                body = json.loads(raw.decode())
                idea = body["idea"]
                count = int(body.get("count") or 3)
                planner = body.get("model") or "grok-4.3"
                job_id = enqueue("escenas", f"Estructurar {count} escenas", lambda: {"scenes": plan_scenes(idea, count, planner)}, {"idea": idea, "count": count, "model": planner, "default_image": body.get("default_image") or ""})
                self.send_json({"job": job_id})
                return
            if path == "/api/scenes":
                body = json.loads(raw.decode())
                scenes = body.get("scenes") or []
                default_image = body.get("default_image") or ""
                base_video = body.get("base_video") or ""
                job_id = enqueue("escena", f"Generar {len(scenes)} escenas", lambda: {"videos": run_scenes(scenes, default_image, base_video), "folder": str(OUTPUT)}, {"scenes": scenes, "default_image": default_image, "base_video": base_video, "aspect": body.get("aspect") or ""})
                self.send_json({"job": job_id})
                return
            if path == "/api/audio":
                body = json.loads(raw.decode())
                model = body.get("model") or "google/gemini-3-8-flash-lite-tts"
                prompt = body["prompt"]
                seconds = int(body["seconds"]) if body.get("seconds") else None
                voice = body.get("voice") or ""
                job_id = enqueue("audio", f"Diálogo · {model}", lambda: make_audio(model, prompt, seconds, voice), {"model": model, "prompt": prompt, "seconds": seconds, "voice": voice, "kind": "audio"})
                self.send_json({"job": job_id})
                return
            if path == "/api/reference":
                body = json.loads(raw.decode())
                model = body.get("model") or "seedance-ref"
                prompt = body["prompt"]
                aspect = body.get("aspect") or "16:9"
                duration = body.get("duration")
                characters = body.get("characters") or []
                scene_image = body.get("scene_image") or ""
                job_id = enqueue(
                    "referencia",
                    f"Referencia · {model}",
                    lambda: make_reference(model, prompt, aspect, duration, characters, scene_image, body.get("resolution") or ""),
                    {"model": model, "prompt": prompt, "aspect": aspect, "duration": duration, "characters": characters, "scene_image": scene_image},
                )
                self.send_json({"job": job_id})
                return
            if path == "/api/image":
                body = json.loads(raw.decode())
                image = Path(body["image_path"]) if body.get("image_path") else None
                model = body.get("model") or "grok"
                prompt = body["prompt"]
                aspect = body.get("aspect") or "16:9"
                resolution = body.get("resolution") or "1K"
                label = "Editar imagen" if image else "Crear imagen"
                job_id = enqueue("imagen", f"{label} · {model}", lambda: make_image(model, prompt, image, aspect, resolution), {"model": model, "prompt": prompt, "image_path": str(image) if image else "", "aspect": aspect, "resolution": resolution, "action": "edit" if image else "create"})
                self.send_json({"job": job_id})
                return
            if path == "/api/frame":
                body = json.loads(raw.decode())
                frame = last_frame(Path(body["file_path"]))
                self.send_json({"file": str(frame)})
                return
            if path == "/api/generate":
                body = json.loads(raw.decode())
                image = Path(body["image_path"]) if body.get("image_path") else None
                model = body.get("model") or "grok"
                prompt = body["prompt"]
                duration = body.get("duration")
                aspect = body.get("aspect") or "16:9"
                characters = body.get("characters") or []
                resolution = body.get("resolution") or ""
                job_id = enqueue("video", f"Video · {model}", lambda: generate(model, prompt, image, duration, aspect, characters, resolution), {"model": model, "prompt": prompt, "image_path": str(image) if image else "", "duration": duration, "aspect": aspect, "characters": characters, "resolution": resolution})
                self.send_json({"job": job_id})
                return
            if path == "/api/trim":
                body = json.loads(raw.decode())
                file_path = body["file_path"]
                start_time = str(body["start_time"])
                end_time = str(body["end_time"])
                job_id = enqueue("video", "Recortar video", lambda: {"result": ffmpeg_mcp("ffmpeg_trim", {"file_path": file_path, "start_time": start_time, "end_time": end_time}), "folder": str(OUTPUT)})
                self.send_json({"job": job_id})
                return
            self.send_error(404)
        except Exception as error:
            self.send_json({"error": str(error)}, 400)


def pick_path(kind: str) -> str:
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if kind == "video":
        types = [("Videos", "*.mp4 *.mov *.webm *.mkv"), ("Todos", "*.*")]
        title = "Seleccionar video"
    elif kind == "media":
        types = [("Imágenes y videos", "*.png *.jpg *.jpeg *.webp *.gif *.mp4 *.mov *.webm *.mkv"), ("Todos", "*.*")]
        title = "Seleccionar archivo"
    elif kind == "audio":
        types = [("Audio", "*.mp3 *.wav *.m4a *.ogg"), ("Todos", "*.*")]
        title = "Seleccionar audio"
    else:
        types = [("Imágenes", "*.png *.jpg *.jpeg *.webp *.gif"), ("Todos", "*.*")]
        title = "Seleccionar imagen"
    chosen = filedialog.askopenfilename(title=title, filetypes=types)
    root.destroy()
    return chosen or ""


JOBS: list[dict] = []
JOBS_LOCK = threading.Lock()


def enqueue(kind: str, title: str, work, inputs: dict | None = None) -> str:
    job = {
        "id": uuid.uuid4().hex[:8],
        "kind": kind,
        "title": title,
        "state": "queued",
        "error": "",
        "files": [],
        "folder": "",
        "inputs": inputs or {},
        "result": None,
        "session_id": SESSION_ID,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with JOBS_LOCK:
        JOBS.insert(0, job)
    save_job(job)

    def run() -> None:
        with JOBS_LOCK:
            job["state"] = "running"
        try:
            result = work()
            files = []
            folder = ""
            if isinstance(result, dict):
                if result.get("file"):
                    files = [result["file"]]
                elif result.get("videos"):
                    files = [item.get("file") for item in result["videos"] if item.get("file")]
                folder = result.get("folder") or (str(Path(files[0]).parent) if files else "")
            credits, usd, provider = cost_of(result)
            with JOBS_LOCK:
                job["state"] = "done"
                job["result"] = result
                job["files"] = files
                job["folder"] = folder
                job["credits"] = credits
                job["usd"] = usd
                job["provider"] = provider
            save_job(job)
        except Exception as error:
            with JOBS_LOCK:
                job["state"] = "error"
                job["error"] = str(error)
            save_job(job)

    threading.Thread(target=run, daemon=True).start()
    return job["id"]


def cost_of(result) -> tuple[float, float, str]:
    if not isinstance(result, dict):
        return 0, 0, ""
    items = result.get("videos") or [result]
    credits = sum(float(item.get("credits") or 0) for item in items if isinstance(item, dict))
    usd = sum(float(item.get("usd") or 0) for item in items if isinstance(item, dict))
    provider = "kie" if credits else ("grok" if usd else "")
    if credits and not usd:
        usd = credits * 0.005
    return credits, usd, provider


DB_PATH = from_env("STUDIO_DB", str(HARNESS / "config" / "mcp" / "studio.db"))
SCHEMA = ROOT / "schema.sql"
SESSION_ID = uuid.uuid4().hex[:12]
MXN_RATE = 18.38


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with db() as connection:
        connection.executescript(SCHEMA.read_text(encoding="utf-8"))
        connection.execute(
            "INSERT OR IGNORE INTO sessions(id, started_at, machine) VALUES (?, ?, ?)",
            (SESSION_ID, time.strftime("%Y-%m-%d %H:%M:%S"), socket.gethostname()),
        )
    import_json_history()


def job_from_row(row: sqlite3.Row) -> dict:
    result = json.loads(row["result_json"]) if row["result_json"] else None
    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "kind": row["kind"],
        "title": row["title"],
        "state": row["state"],
        "error": row["error"],
        "files": json.loads(row["files_json"] or "[]"),
        "folder": row["folder"],
        "inputs": json.loads(row["inputs_json"] or "{}"),
        "result": result,
        "credits": row["credits"],
        "usd": row["usd"],
        "provider": row["provider"],
    }


def save_job(job: dict) -> None:
    result = job.get("result")
    if isinstance(result, dict) and result.get("scenes"):
        result = {"scenes": result["scenes"]}
    elif not isinstance(result, dict):
        result = None
    with db() as connection:
        connection.execute(
            """
            INSERT INTO jobs(id, session_id, kind, title, state, error, files_json, folder, inputs_json, result_json, credits, usd, provider, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                state=excluded.state, error=excluded.error, files_json=excluded.files_json,
                folder=excluded.folder, result_json=excluded.result_json, credits=excluded.credits,
                usd=excluded.usd, provider=excluded.provider
            """,
            (
                job["id"],
                job.get("session_id") or SESSION_ID,
                job.get("kind") or "",
                job.get("title") or "",
                job.get("state") or "",
                job.get("error") or "",
                json.dumps(job.get("files") or [], ensure_ascii=False),
                job.get("folder") or "",
                json.dumps(job.get("inputs") or {}, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False) if result else None,
                float(job.get("credits") or 0),
                float(job.get("usd") or 0),
                job.get("provider") or "",
                job.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )


def load_history() -> None:
    with db() as connection:
        rows = connection.execute(
            "SELECT * FROM jobs WHERE session_id = ? ORDER BY created_at DESC",
            (SESSION_ID,),
        ).fetchall()
    with JOBS_LOCK:
        JOBS.extend(job_from_row(row) for row in rows)


def import_json_history() -> None:
    legacy = from_env("STUDIO_HISTORY", str(HARNESS / "config" / "mcp" / "studio-history.json"))
    if not legacy.is_file():
        return
    with db() as connection:
        already = connection.execute("SELECT 1 FROM sessions WHERE id = 'importado'").fetchone()
    if already:
        return
    try:
        saved = json.loads(legacy.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    with db() as connection:
        connection.execute(
            "INSERT INTO sessions(id, started_at, machine) VALUES ('importado', ?, ?)",
            (time.strftime("%Y-%m-%d %H:%M:%S"), "json"),
        )
    for item in saved:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        item["session_id"] = "importado"
        save_job(item)


BILLING_AT = 0.0
BILLING_DATA: dict = {}


def billing() -> dict:
    global MXN_RATE, BILLING_AT, BILLING_DATA
    if time.time() - BILLING_AT > 30 or not BILLING_DATA:
        fresh = {"kie_credits": None, "kie_error": ""}
        try:
            quote = http_json("GET", "https://api.frankfurter.dev/v1/latest?from=USD&to=MXN", timeout=15)
            MXN_RATE = float(quote["rates"]["MXN"])
        except Exception:
            pass
        try:
            body = http_json(
                "GET",
                "https://api.kie.ai/api/v1/chat/credit",
                headers={"Authorization": f"Bearer {kie_key()}", "Accept": "application/json"},
                timeout=20,
            )
            fresh["kie_credits"] = body.get("data")
        except Exception as error:
            fresh["kie_error"] = str(error)
        BILLING_DATA = fresh
        BILLING_AT = time.time()
    with JOBS_LOCK:
        kie_usd = sum(float(job.get("usd") or 0) for job in JOBS if job.get("provider") == "kie")
        grok_usd = sum(float(job.get("usd") or 0) for job in JOBS if job.get("provider") == "grok")
    return {
        "mxn_rate": MXN_RATE,
        "kie_credits": BILLING_DATA.get("kie_credits"),
        "kie_error": BILLING_DATA.get("kie_error") or "",
        "kie_usd": kie_usd,
        "kie_mxn": kie_usd * MXN_RATE,
        "grok_usd": grok_usd,
        "grok_mxn": grok_usd * MXN_RATE,
        "grok_balance": None,
    }


init_db()
load_history()


def job_snapshot() -> list[dict]:
    with JOBS_LOCK:
        return [dict(job) for job in JOBS]


def open_folder(path: str) -> None:
    folder = Path(path).resolve()
    allowed = MEDIA.resolve()
    if allowed not in folder.parents and folder != allowed:
        raise RuntimeError(f"Carpeta fuera de {MEDIA}")
    if not folder.is_dir():
        raise RuntimeError("La carpeta no existe")
    os.startfile(folder)


def serve() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    IMAGES.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        return
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()


def main() -> None:
    serve()
    if "--mcp" in sys.argv:
        from mcp.server.fastmcp import FastMCP

        studio = FastMCP("video-studio")

        @studio.tool()
        def studio_generate(prompt: str, model: str = "grok", image_path: str = "", duration: int = 0) -> str:
            """Generate a video. Default model is grok. Kie ids: seedance-1-pro, seedance-1-5, seedance-2-mini."""
            image = Path(image_path) if image_path else None
            return json.dumps(generate(model, prompt, image, duration or None), ensure_ascii=False)

        @studio.tool()
        def studio_trim(file_path: str, start_time: str, end_time: str) -> str:
            """Trim a video through the FFmpeg editor MCP."""
            return ffmpeg_mcp("ffmpeg_trim", {
                "file_path": file_path,
                "start_time": start_time,
                "end_time": end_time,
            })

        @studio.tool()
        def studio_gui() -> str:
            """Return the local GUI URL. The page is already running."""
            return f"http://127.0.0.1:{PORT}"

        studio.run()
    else:
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        threading.Event().wait()


if __name__ == "__main__":
    main()
