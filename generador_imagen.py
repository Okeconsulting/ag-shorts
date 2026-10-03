import json
import os
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont
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

def generar_portada_titulo(titulo: str, ruta_salida: str) -> str:
    """
    Genera la imagen de la Escena 1 (portada del short en 1080x1920 nativo):
    - Título del guion en caligrafía legible y nítida.
    - Estilo en tonos claros, elegante y comercial, armonizado con la identidad de Okeconsulting.
    - Distribución equilibrada que deja el tercio inferior libre para el subtítulo dinámico.
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    ancho, alto = 1080, 1920
    img = Image.new("RGB", (ancho, alto), color="#FAF8F5")
    draw = ImageDraw.Draw(img)

    # Degradado vertical sutil de fondo
    for y in range(alto):
        factor = y / alto
        r = int(250 - factor * 14)
        g = int(248 - factor * 16)
        b = int(245 - factor * 18)
        draw.line([(0, y), (ancho, y)], fill=(r, g, b))

    card_w, card_h = 960, 1220
    card_x0 = (ancho - card_w) // 2
    card_y0 = 300
    card_x1 = card_x0 + card_w
    card_y1 = card_y0 + card_h

    # Sombra suave de la tarjeta
    for offset in range(16, 0, -2):
        draw.rounded_rectangle(
            [card_x0 - offset, card_y0 - offset, card_x1 + offset, card_y1 + offset],
            radius=44,
            fill=(225, 220, 212)
        )
    draw.rounded_rectangle(
        [card_x0, card_y0, card_x1, card_y1],
        radius=38,
        fill="#FFFFFF",
        outline="#E8E2D8",
        width=3
    )

    # 1. Badge superior institucional
    font_badge = None
    for fb in ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"]:
        try:
            font_badge = ImageFont.truetype(fb, 32)
            break
        except Exception:
            continue
    if not font_badge:
        font_badge = ImageFont.load_default()

    b_txt = "OKECONSULTING • PYMES"
    bb = draw.textbbox((0, 0), b_txt, font=font_badge)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = bw + 56, bh + 24
    px0, py0 = (ancho - pw) // 2, card_y0 + 60
    draw.rounded_rectangle([px0, py0, px0 + pw, py0 + ph], radius=22, fill="#F6ECE1")
    draw.text(((ancho - bw) // 2, py0 + 12), b_txt, font=font_badge, fill="#8B4513")

    # 2. Tipografía del Título en caligrafía legible
    # Prioridad: Lucida Calligraphy (LCALLIG.TTF) -> Gabriola -> Georgia Bold -> Segoe UI Bold
    font_t = None
    for f_name, size in [("LCALLIG.TTF", 78), ("Gabriola.ttf", 125), ("georgiab.ttf", 75), ("segoeuib.ttf", 72)]:
        try:
            font_t = ImageFont.truetype(f_name, size)
            break
        except Exception:
            continue
    if not font_t:
        font_t = ImageFont.load_default()

    lineas = textwrap.wrap(titulo, width=20)
    line_heights = [draw.textbbox((0, 0), l, font=font_t)[3] - draw.textbbox((0, 0), l, font=font_t)[1] for l in lineas]
    interlineado = 22
    bloque_h = sum(line_heights) + interlineado * (len(lineas) - 1)

    y_texto = card_y0 + 180 + (480 - bloque_h) // 2
    for idx, l in enumerate(lineas):
        bb_l = draw.textbbox((0, 0), l, font=font_t)
        lw = bb_l[2] - bb_l[0]
        lx = (ancho - lw) // 2
        draw.text((lx, y_texto), l, font=font_t, fill="#181822", stroke_width=1, stroke_fill="#181822")
        y_texto += line_heights[idx] + interlineado

    # 3. Línea divisoria ámbar / dorada
    div_w = 160
    div_y = y_texto + 35
    draw.rounded_rectangle([(ancho - div_w) // 2, div_y, (ancho + div_w) // 2, div_y + 6], radius=3, fill="#D97706")

    # 4. Detalle decorativo
    font_sub = None
    for fs in ["segoeui.ttf", "arial.ttf", "calibri.ttf"]:
        try:
            font_sub = ImageFont.truetype(fs, 28)
            break
        except Exception:
            continue
    if not font_sub:
        font_sub = ImageFont.load_default()

    sub_txt = "Aprende en 60 segundos"
    bb_s = draw.textbbox((0, 0), sub_txt, font=font_sub)
    draw.text(((ancho - (bb_s[2] - bb_s[0])) // 2, div_y + 25), sub_txt, font=font_sub, fill="#9CA3AF")

    img.save(ruta_salida, format="PNG")
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

def _generar_con_huggingface(prompt: str, hf_token: str, seed: int = None):
    """Descarga la imagen usando Hugging Face Serverless (FLUX.1-schnell gratuito)."""
    from huggingface_hub import InferenceClient
    client = InferenceClient(token=hf_token)
    return client.text_to_image(prompt[:850], model="black-forest-labs/FLUX.1-schnell")

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

    # Cargar imagen devuelta (puede ser PIL.Image o bytes)
    if isinstance(datos_imagen, Image.Image):
        img_raw = datos_imagen.convert("RGB")
    else:
        img_raw = Image.open(BytesIO(datos_imagen)).convert("RGB")

    # FASE 1 DE NITIDEZ: Upscaling de alta fidelidad Lanczos a 1080x1920 nativo
    img_upscaled = ImageOps.fit(img_raw, (1080, 1920), method=Image.Resampling.LANCZOS)

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
    - Escena 1 usa la portada con el título del guion en caligrafía legible y diseño nítido.
    - Escena 2 y escena N (última) usan la imagen corporativa oficial avatar/avatar.jpg.
    - Escenas intermedias (3 a N-1) usan FLUX con semilla vinculada (Seed Locking) y súper-resolución nítida.
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
        print(f"[Fase 4] Avatar corporativo detectado en: '{ruta_avatar}' (asignado a escena 2 y escena {total_escenas})")
    else:
        print(f"[Fase 4] Advertencia: No se encontró 'avatar/avatar.jpg', se generarán con FLUX las escenas no-portada.")

    print(f"\n[Fase 4] Produciendo {total_escenas} imágenes NÍTIDAS (estilo 3D tonos claros, 1080x1920) en '{carpeta_salida}'...")

    for idx, escena in enumerate(escenas, start=1):
        escena_id = escena.get("id_escena", escena.get("escena_id", idx))
        ruta = os.path.join(carpeta_salida, f"img_{escena_id}.png")

        if idx == 1:
            # Escena 1: Portada con título del guion en caligrafía legible
            generar_portada_titulo(titulo_video, ruta)
            print(f"[Fase 4 - Portada Título] Escena {idx}/{total_escenas}: Portada tipográfica legible -> {ruta}")
            rutas_imagenes.append(ruta)
        elif (idx == 2 or idx == total_escenas) and ruta_avatar:
            # Escena 2 y Escena Final: Avatar corporativo oficial
            preparar_imagen_avatar(ruta_avatar, ruta)
            print(f"[Fase 4 - Avatar Oficial] Escena {idx}/{total_escenas}: Imagen de marca fijada -> {ruta}")
            rutas_imagenes.append(ruta)
        else:
            # Escenas intermedias: Generación con FLUX y súper-resolución
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
