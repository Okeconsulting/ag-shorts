import os
import sys
import time
import urllib.parse
import urllib.request
from io import BytesIO
from PIL import Image, ImageOps

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    conservando la proporción original mediante recorte inteligente y Lanczos.
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with Image.open(ruta_avatar) as img:
        img_rgb = img.convert("RGB")
        img_fitted = ImageOps.fit(img_rgb, (1080, 1920), method=Image.Resampling.LANCZOS)
        img_fitted.save(ruta_salida, format="PNG")
    return ruta_salida

def generar_imagen_escena(prompt: str, ruta_salida: str, estilo_global: str = "") -> str:
    """
    Genera una imagen fotorrealista en formato vertical 9:16 (1080x1920) utilizando el motor visual FLUX.
    Mantiene estrictamente una paleta de tonos claros, moderna, luminosa y orientada a Pymes.
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

    estilo_tonos_claros = "bright light tones, clean modern aesthetic, soft natural daylight, minimalist bright office and business atmosphere, high quality, 9:16 vertical orientation, no dark gloomy shadows, no text, no letters"

    prompt_completo = prompt
    if estilo_global and estilo_global not in prompt:
        prompt_completo = f"{prompt}, visual style: {estilo_global}, {estilo_tonos_claros}"
    elif "light tones" not in prompt_completo.lower():
        prompt_completo = f"{prompt}, {estilo_tonos_claros}"

    print(f"[Fase 4 - FLUX] Generando escena: '{prompt_completo[:65]}...'")

    prompt_codificado = urllib.parse.quote(prompt_completo[:350])
    # Parámetros exactos para YouTube Shorts: 1080x1920 (9:16 vertical), motor FLUX, sin marca de agua
    url = f"https://image.pollinations.ai/prompt/{prompt_codificado}?width=1080&height=1920&model=flux&nologo=true"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Okeconsulting-Shorts-Engine/1.0 (Windows; Python)"}
    )

    max_reintentos = 3
    for intento in range(1, max_reintentos + 1):
        try:
            with urllib.request.urlopen(req, timeout=50) as respuesta:
                datos_imagen = respuesta.read()

            img = Image.open(BytesIO(datos_imagen))
            img.save(ruta_salida, format="PNG")
            print(f"[FLUX] Imagen guardada con éxito en: {ruta_salida} ({img.width}x{img.height})")
            return ruta_salida
        except Exception as e:
            if intento == max_reintentos:
                raise RuntimeError(f"Error descargando imagen con FLUX tras {max_reintentos} intentos: {e}")
            print(f"  [FLUX] Conexión lenta o reintento {intento}/{max_reintentos}... esperando 4s.")
            time.sleep(4)

def generar_imagenes_desde_json(datos_json: dict, carpeta_salida: str = "assets") -> list:
    """
    Itera sobre las escenas del JSON y genera las imágenes en 'carpeta_salida/img_{id}.png'.
    - La primera escena (img_1.png) y la última escena (img_N.png) usan avatar/avatar.jpg.
    - Las escenas intermedias se generan con FLUX en formato vertical 9:16 en tonos claros.
    - Aplica pausa preventiva de 5 segundos solo entre descargas remotas de FLUX.
    Retorna la lista de rutas generadas.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    estilo_global = datos_json.get("estilo_visual_global", "")
    escenas = datos_json.get("escenas", [])
    rutas_imagenes = []
    total_escenas = len(escenas)

    ruta_avatar = obtener_ruta_avatar()
    if ruta_avatar:
        print(f"[Fase 4] Avatar corporativo detectado en: '{ruta_avatar}' (se asignará a escena 1 y escena {total_escenas})")
    else:
        print(f"[Fase 4] Advertencia: No se encontró 'avatar/avatar.jpg', se generarán todas las escenas con FLUX.")

    print(f"\n[Fase 4] Generando {total_escenas} imágenes (estilo tonos claros, 9:16 vertical) en '{carpeta_salida}'...")

    for idx, escena in enumerate(escenas, start=1):
        escena_id = escena.get("id_escena", escena.get("escena_id", idx))
        ruta = os.path.join(carpeta_salida, f"img_{escena_id}.png")

        es_primera_o_ultima = (idx == 1 or idx == total_escenas)

        if es_primera_o_ultima and ruta_avatar:
            preparar_imagen_avatar(ruta_avatar, ruta)
            print(f"[Fase 4 - Avatar Oficial] Escena {idx}/{total_escenas}: Imagen de marca fijada con éxito -> {ruta}")
            rutas_imagenes.append(ruta)
        else:
            generar_imagen_escena(
                prompt=escena["prompt_imagen"],
                ruta_salida=ruta,
                estilo_global=estilo_global
            )
            rutas_imagenes.append(ruta)

            # Pausa preventiva de 5 segundos solo después de descargas web FLUX
            # (no es necesaria si la siguiente escena es la última y usa el avatar local)
            siguiente_es_avatar = ((idx + 1 == total_escenas) and (ruta_avatar is not None))
            if idx < total_escenas and not siguiente_es_avatar:
                print(f"[Fase 4] Pausa preventiva de 5 segundos antes de la escena {idx + 1}/{total_escenas}...")
                time.sleep(5)

    print(f"[Fase 4] Todas las imágenes ({len(rutas_imagenes)}) fueron generadas exitosamente.")
    return rutas_imagenes
