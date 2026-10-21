# Estudio de video MCP

MCP y interfaz local para crear videos, imágenes, diálogos y referencias.

Usa la **sesión de Grok** conectada en DeepSeek Harness (OAuth de xAI, la misma que usa Grok Build) y, como opción de pago, la **API de Kie**. Grok queda por defecto. Kie se usa para Seedance, Seedream, voces baratas y modelos de referencia.

Por ahora solo se ha usado en un harness local de DSH, con el build de DeepSeek. No está probado en otro entorno.

## Qué incluye

- GUI en `http://127.0.0.1:7474`: video, escenas, imagen, audio, referencias, edición e historial.
- Servidor MCP por stdio, con `--mcp`.
- Herramientas MCP:
  - `studio_generate`: genera un video. El modelo por defecto es `grok`.
  - `studio_trim`: recorta con el MCP de FFmpeg, si está instalado.
  - `studio_gui`: devuelve la URL de la interfaz.

## Dependencias

- Python 3.10 o superior.
- Paquete Python: `mcp>=1.9,<2`. La versión 2 quitó `mcp.server.fastmcp`.
- FFmpeg en el `PATH`, o `FFMPEG_PATH` apuntando a `ffmpeg.exe`. También hace falta `ffprobe` al lado.
- Para recortar desde el MCP: [ffmpeg-mcp-lite](https://github.com/kevinwatt/ffmpeg-mcp-lite), con `FFMPEG_MCP` apuntando a su ejecutable.
- Sesión de Grok. En DSH local está en `%USERPROFILE%\.dsh\.xai-oauth-auth.json` después de conectar xAI. Fuera de DSH se puede usar `XAI_API_KEY` o `GROK_TOKEN`.
- Key de Kie, solo si vas a usar modelos de pago. Una línea en un archivo, o la variable `KIE_API_KEY`. No la subas al repositorio.

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Interfaz:

```powershell
.\.venv\Scripts\python.exe app.py
```

MCP, para DSH u otro cliente stdio:

```powershell
.\.venv\Scripts\python.exe app.py --mcp
```

Hay un ejemplo de registro en [config/video-studio.cordis.yml](config/video-studio.cordis.yml). En DSH el `serverName` debe ser `[A-Za-z0-9_-]{1,32}`. Las herramientas aparecen como `mcp_video_studio_...` después de recargar el perfil.

## Variables

| Variable | Uso |
| --- | --- |
| `HARNESS_HOME` | Carpeta base. Por defecto `D:\harnes-code`. |
| `STUDIO_MEDIA` | Carpeta de salida. Por defecto `videos` dentro de `HARNESS_HOME`. |
| `GROK_OAUTH_FILE` | JSON de la sesión OAuth de xAI. |
| `XAI_API_KEY` o `GROK_TOKEN` | Token directo, si no hay archivo OAuth. |
| `KIE_API_KEY` | Key de Kie. |
| `KIE_KEY_FILE` | Archivo de una línea con la key de Kie. |
| `FFMPEG_PATH` | `ffmpeg.exe`. |
| `FFMPEG_MCP` | Ejecutable de ffmpeg-mcp-lite. |
| `STUDIO_HISTORY` | JSON del historial y los costos. |

La carpeta de video se llama `ouput` a propósito. No la renombres si ya tienes archivos ahí.

## Modelos

- Grok de la sesión: video Imagine 1.5, imagen Imagine 2.0, texto a voz y extensión nativa con `grok-imagine-video`.
- Kie: Seedance 1.0 Lite, Pro Fast, Pro, 1.5 Pro, 2.0 Fast, 2.0, 2.0 Mini, 2.5 Draft y Seedream.
- Audio de Kie: Gemini Flash y ElevenLabs. El tipo de voz y la demo solo aparecen cuando el modelo las publica.
- Referencias: solo modelos que aceptan imagen, audio o personajes.

Los costos de Kie que muestra la interfaz son estimados. Grok no descuenta créditos de Kie; se cobra a la sesión de xAI.

## Qué no va en este repositorio

No se incluyen la key de Kie, el token de la sesión, el entorno virtual, FFmpeg ni los videos generados. Este código se escribió y probó solo en el harness local de DSH.
