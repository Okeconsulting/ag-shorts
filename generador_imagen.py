import os
import sys
import time
import urllib.parse
import urllib.request
from io import BytesIO
from PIL import Image

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def generar_imagen_escena(prompt: str, ruta_salida: str, estilo_global: str = "") -> str:
    """
    Genera una imagen fotorrealista en formato vertical 9:16 (1080x1920) utilizando el motor visual FLUX.
    Es 100% gratuito, sin necesidad de API Key ni cuotas de Google.
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

    prompt_completo = prompt
    if estilo_global and estilo_global not in prompt:
        prompt_completo = f"{prompt}, visual style: {estilo_global}, high quality, 9:16 vertical orientation, no text"

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
    Itera sobre las escenas del JSON y genera las imágenes en 'carpeta_salida/img_{id}.png' usando FLUX (9:16).
    Aplica una pausa preventiva de 5 segundos entre cada descarga.
    Retorna la lista de rutas generadas.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    estilo_global = datos_json.get("estilo_visual_global", "")
    escenas = datos_json.get("escenas", [])
    rutas_imagenes = []
    total_escenas = len(escenas)

    print(f"\n[Fase 4] Generando {total_escenas} imágenes con motor FLUX (9:16 vertical gratuito) en '{carpeta_salida}'...")
    for idx, escena in enumerate(escenas, start=1):
        escena_id = escena.get("id_escena", escena.get("escena_id", idx))
        ruta = os.path.join(carpeta_salida, f"img_{escena_id}.png")
        generar_imagen_escena(
            prompt=escena["prompt_imagen"],
            ruta_salida=ruta,
            estilo_global=estilo_global
        )
        rutas_imagenes.append(ruta)

        # Pausa preventiva de 5 segundos entre cada generación
        if idx < total_escenas:
            print(f"[Fase 4] Pausa preventiva de 5 segundos antes de la escena {idx + 1}/{total_escenas}...")
            time.sleep(5)

    print(f"[Fase 4] Todas las imágenes ({len(rutas_imagenes)}) fueron generadas exitosamente con FLUX.")
    return rutas_imagenes
