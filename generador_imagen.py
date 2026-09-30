import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO
from PIL import Image, ImageOps, ImageFilter
from dotenv import load_dotenv

load_dotenv()

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ------------------------------------------------------------------------------
# CONSTANTES DE ESTILO MAESTRO Y NITIDEZ
# ------------------------------------------------------------------------------
# Estilo maestro de renderizado y luz (sin forzar muebles específicos de oficina
# para permitir que el sujeto concreto de cada escena brille según el guion).
ESTILO_MAESTRO_3D = (
    "clean minimalist 3D stylized render, elegant Pixar and Apple tech aesthetics, "
    "bright soft daylight, luminous light tones, crisp geometry, smooth textures, "
    "vibrant clean colors, professional commercial composition"
)

MODIFICADORES_NITIDEZ_POSITIVOS = (
    "ultra sharp focus, crisp fine details, 8k uhd, clean sharp edges, macro lens clarity, "
    "commercial lighting, high fidelity, 9:16 vertical orientation"
)

MODIFICADORES_NEGATIVOS = (
    "no blur, no depth of field blur, no bokeh, no motion blur, no lowres, no haze, "
    "no grainy textures, no compression artifacts, no distorted anatomy, no dark gloomy shadows, "
    "no text, no letters, no watermark, no logos"
)

def obtener_ruta_avatar() -> str | None:
    """Busca la imagen oficial del avatar en las rutas posibles del proyecto."""
    rutas_posibles = [
        os.path.join("avatar", "avatar.jpg"),
        os.path.join("avatar", "avatar.png"),
        os.path.join("avatar", "avatar.jpeg"),
        "avatar.jpg",
        "avatar.png"
    ]
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            return ruta
    return None

def preparar_imagen_avatar(ruta_avatar: str, ruta_salida: str) -> str:
    """
    Ajusta la imagen del avatar oficial exactamente a 1080x1920 (9:16 vertical)
    conservando la proporción original mediante recorte inteligente y Lanczos de alta nitidez.
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with Image.open(ruta_avatar) as img:
        img_rgb = img.convert("RGB")
        img_fitted = ImageOps.fit(img_rgb, (1080, 1920), method=Image.Resampling.LANCZOS)
        img_fitted.save(ruta_salida, format="PNG")
    return ruta_salida

def _generar_con_pollinations(prompt: str, api_key: str = "", seed: int = None) -> bytes:
    """Descarga la imagen desde Pollinations AI usando FLUX."""
    prompt_codificado = urllib.parse.quote(prompt[:850])
    param_seed = f"&seed={seed}" if seed is not None else ""
    param_key = f"&key={api_key}" if api_key else ""
    url = f"https://image.pollinations.ai/prompt/{prompt_codificado}?width=1080&height=1920&model=flux&nologo=true{param_seed}{param_key}"

    headers = {
        "User-Agent": "Okeconsulting-Shorts-Engine/2.0 (Windows; Python)"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=55) as respuesta:
        return respuesta.read()

def _generar_con_huggingface(prompt: str, hf_token: str, seed: int = None) -> bytes:
    """Descarga la imagen desde Hugging Face Serverless (FLUX.1-schnell gratuito)."""
    url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    payload = json.dumps({
        "inputs": prompt[:850],
        "parameters": {"width": 576, "height": 1024}
    }).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
        "User-Agent": "Okeconsulting-Shorts-Engine/2.0 (Windows; Python)"
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as respuesta:
        return respuesta.read()

def generar_imagen_escena(prompt: str, ruta_salida: str, estilo_global: str = "", seed: int = None) -> str:
    """
    Genera una imagen fotorrealista/3D en formato vertical 9:16 (1080x1920) utilizando FLUX.
    - Soporta Pollinations (con API Key gratuita opcional) y Hugging Face Serverless (HF_TOKEN gratuito).
    - Respeta rigurosamente el sujeto y acción concreta al inicio del prompt.
    - Aplica modificadores de ultra nitidez y estilo maestro en tonos claros.
    - Soporta fijación de semilla (seed) para máxima coherencia visual entre escenas.
    - Super-resolución local con Lanczos y máscara de enfoque adaptativa (UnsharpMask)
      para eliminar definitivamente cualquier desenfoque o pérdida de definición.
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

    estilo_aplicar = estilo_global or ESTILO_MAESTRO_3D

    # El prompt generado por el Director Técnico YA contiene el sujeto concreto al inicio.
    partes_prompt = [prompt.strip().rstrip(".")]

    # Solo complementar el estilo si el prompt no contiene ya descriptores de estilo 3D
    if "3d" not in prompt.lower() and "render" not in prompt.lower():
        partes_prompt.append(estilo_aplicar)
    elif estilo_global and estilo_global not in prompt:
        partes_prompt.append(estilo_global)

    # Agregar modificadores de nitidez óptica y negativos si no están ya en el prompt
    if "ultra sharp" not in prompt.lower() and "sharp focus" not in prompt.lower():
        partes_prompt.append(MODIFICADORES_NITIDEZ_POSITIVOS)
    if "no blur" not in prompt.lower():
        partes_prompt.append(MODIFICADORES_NEGATIVOS)

    prompt_completo = ", ".join(partes_prompt)

    api_key_pollinations = os.getenv("POLLINATIONS_API_KEY", "").strip()
    hf_token = os.getenv("HF_TOKEN", "").strip()

    motor_activo = "Hugging Face (FLUX.1-schnell)" if (hf_token and not api_key_pollinations) else "Pollinations (FLUX HD)"
    print(f"[Fase 4 - {motor_activo}] Generando escena: '{prompt_completo[:75]}...' (seed={seed})")

    datos_imagen = None
    max_reintentos = 3

    # 1. Intentar con Hugging Face si está configurado
    if hf_token and not api_key_pollinations:
        for intento in range(1, max_reintentos + 1):
            try:
                datos_imagen = _generar_con_huggingface(prompt_completo, hf_token, seed=seed)
                break
            except Exception as e:
                if intento == max_reintentos:
                    print(f"  [Hugging Face] Error tras {max_reintentos} intentos: {e}. Probando Pollinations...")
                else:
                    time.sleep(3)

    # 2. Intentar con Pollinations si aún no hay imagen
    if not datos_imagen:
        for intento in range(1, max_reintentos + 1):
            try:
                datos_imagen = _generar_con_pollinations(prompt_completo, api_key=api_key_pollinations, seed=seed)
                break
            except urllib.error.HTTPError as e:
                if e.code == 402 or e.code == 401:
                    # Si falla con 402/401 y tenemos HF_TOKEN disponible, saltar a HF
                    if hf_token:
                        print(f"  [Aviso 402] Pollinations requirió créditos. Cambiando automáticamente a Hugging Face Serverless...")
                        try:
                            datos_imagen = _generar_con_huggingface(prompt_completo, hf_token, seed=seed)
                            break
                        except Exception as hf_err:
                            print(f"  [Hugging Face] Error de respaldo: {hf_err}")

                    mensaje_ayuda = (
                        "\n" + "="*70 + "\n"
                        "❌ [ERROR 402: PAGO / LÍMITE DE CUOTA ALCANZADO EN POLLINATIONS]\n"
                        "Pollinations ha limitado las solicitudes anónimas a 1 imagen/hora para tu dirección IP.\n\n"
                        "💡 CÓMO SOLUCIONARLO 100% GRATIS (SIN PAGAR Y SIN TARJETA DE CRÉDITO):\n\n"
                        "OPCIÓN 1 (Recomendada - 30 segundos):\n"
                        "  1. Entra a: https://enter.pollinations.ai e inicia sesión con tu cuenta de GitHub o Google.\n"
                        "  2. Copia tu API Key gratuita (formato 'sk_...').\n"
                        "  3. Pégala en tu archivo .env:\n"
                        "     POLLINATIONS_API_KEY=sk_tu_clave_aqui\n\n"
                        "OPCIÓN 2 (Hugging Face Serverless - 100% permanente):\n"
                        "  1. Crea un token gratuito en: https://huggingface.co/settings/tokens (tipo 'Read').\n"
                        "  2. Pégalo en tu archivo .env:\n"
                        "     HF_TOKEN=hf_tu_token_aqui\n"
                        "="*70
                    )
                    raise RuntimeError(mensaje_ayuda) from e

                if intento == max_reintentos:
                    raise RuntimeError(f"Error descargando imagen con FLUX tras {max_reintentos} intentos: {e}")
                print(f"  [FLUX HD] Conexión lenta o reintento {intento}/{max_reintentos}... esperando 4s.")
                time.sleep(4)
            except Exception as e:
                if intento == max_reintentos:
                    raise RuntimeError(f"Error descargando imagen con FLUX tras {max_reintentos} intentos: {e}")
                print(f"  [FLUX HD] Conexión lenta o reintento {intento}/{max_reintentos}... esperando 4s.")
                time.sleep(4)

    if not datos_imagen:
        raise RuntimeError("No se pudieron obtener datos binarios de la imagen.")

    # Cargar imagen devuelta por la API
    img_raw = Image.open(BytesIO(datos_imagen)).convert("RGB")

    # FASE 1 DE NITIDEZ: Upscaling de alta fidelidad Lanczos a 1080x1920 nativo
    img_upscaled = img_raw.resize((1080, 1920), Image.Resampling.LANCZOS)

    # FASE 2 DE NITIDEZ: Máscara de enfoque fotográfica para eliminar bordes borrosos
    img_final = img_upscaled.filter(
        ImageFilter.UnsharpMask(radius=1.8, percent=140, threshold=2)
    )

    img_final.save(ruta_salida, format="PNG")
    print(f"[FLUX HD] Imagen nítida guardada con éxito en: {ruta_salida} (1080x1920, seed={seed})")
    return ruta_salida

def generar_imagenes_desde_json(datos_json: dict, carpeta_salida: str = "assets") -> list:
    """
    Itera sobre las escenas del JSON y genera las imágenes en 'carpeta_salida/img_{id}.png'.
    - Escena 1 y escena N usan la imagen corporativa oficial avatar/avatar.jpg.
    - Escenas intermedias usan FLUX con semilla vinculada (Seed Locking) y súper-resolución nítida.
    - Pausa preventiva de 5 segundos solo entre llamadas remotas de FLUX.
    Retorna la lista de rutas generadas.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    estilo_global = datos_json.get("estilo_visual_global", "")
    escenas = datos_json.get("escenas", [])
    rutas_imagenes = []
    total_escenas = len(escenas)

    # Semilla base determinista basada en el título para cohesión de luz, textura y color
    titulo_video = datos_json.get("titulo_video", "video_short")
    seed_base = abs(hash(titulo_video)) % 80000 + 1000

    ruta_avatar = obtener_ruta_avatar()
    if ruta_avatar:
        print(f"[Fase 4] Avatar corporativo detectado en: '{ruta_avatar}' (asignado a escena 1 y escena {total_escenas})")
    else:
        print(f"[Fase 4] Advertencia: No se encontró 'avatar/avatar.jpg', se generarán todas con FLUX.")

    print(f"\n[Fase 4] Produciendo {total_escenas} imágenes NÍTIDAS (estilo 3D tonos claros, 1080x1920) en '{carpeta_salida}'...")

    for idx, escena in enumerate(escenas, start=1):
        escena_id = escena.get("id_escena", escena.get("escena_id", idx))
        ruta = os.path.join(carpeta_salida, f"img_{escena_id}.png")

        es_primera_o_ultima = (idx == 1 or idx == total_escenas)

        if es_primera_o_ultima and ruta_avatar:
            preparar_imagen_avatar(ruta_avatar, ruta)
            print(f"[Fase 4 - Avatar Oficial] Escena {idx}/{total_escenas}: Imagen de marca fijada -> {ruta}")
            rutas_imagenes.append(ruta)
        else:
            # Semilla secuencial vinculada para que todas las escenas intermedias compartan el mismo estilo
            seed_escena = seed_base + (idx * 17)
            generar_imagen_escena(
                prompt=escena["prompt_imagen"],
                ruta_salida=ruta,
                estilo_global=estilo_global,
                seed=seed_escena
            )
            rutas_imagenes.append(ruta)

            # Pausa preventiva de 5 segundos solo después de descargas web FLUX
            siguiente_es_avatar = ((idx + 1 == total_escenas) and (ruta_avatar is not None))
            if idx < total_escenas and not siguiente_es_avatar:
                print(f"[Fase 4] Pausa preventiva de 5 segundos antes de la escena {idx + 1}/{total_escenas}...")
                time.sleep(5)

    print(f"[Fase 4] Todas las imágenes ({len(rutas_imagenes)}) fueron generadas con súper-resolución y nitidez.")
    return rutas_imagenes
