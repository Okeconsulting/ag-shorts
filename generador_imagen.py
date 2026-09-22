import os
import sys
import time
import urllib.parse
import urllib.request
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types
from utils import ejecutar_con_reintentos

load_dotenv()

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def obtener_cliente_imagen() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "tu_api_key" in api_key:
        raise ValueError(
            "No se ha configurado una GEMINI_API_KEY válida en el archivo .env.\n"
            "Consulta INSTRUCCIONES_CONFIGURACION.md para configurar tu clave."
        )
    return genai.Client(api_key=api_key)

def generar_imagen_fallback_flux(prompt: str, ruta_salida: str) -> str:
    """
    Generador de respaldo gratuito (FLUX / SDXL en 1080x1920 vertical)
    en caso de que la API Key de Google no tenga cuota habilitada (limit: 0 en capa gratuita).
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    prompt_limpio = urllib.parse.quote(prompt[:300])
    url = f"https://image.pollinations.ai/prompt/{prompt_limpio}?width=1080&height=1920&model=flux&nologo=true"
    
    req = urllib.request.Request(url, headers={"User-Agent": "Okeconsulting-Shorts-Engine/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
        
    img = Image.open(BytesIO(data))
    img.save(ruta_salida, format="PNG")
    print(f"[Imagen Respaldo FLUX] Guardada exitosamente en: {ruta_salida} ({img.width}x{img.height})")
    return ruta_salida

def generar_imagen_escena(prompt: str, ruta_salida: str, estilo_global: str = "", cliente: genai.Client = None) -> str:
    """
    Genera una imagen vertical 9:16 usando Gemini Developer API con client.models.generate_content(),
    apuntando a 'gemini-3.1-flash-image' con modalidad response_modalities=['IMAGE'].
    """
    client = cliente or obtener_cliente_imagen()
    modelo = os.getenv("IMAGEN_MODEL", "gemini-3.1-flash-image")

    prompt_completo = prompt
    if estilo_global and estilo_global not in prompt:
        prompt_completo = f"{prompt}, visual style: {estilo_global}, high quality, 9:16 vertical orientation, no text"

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    print(f"[Fase 4 - Imagen] Solicitando a '{modelo}': '{prompt_completo[:60]}...'")

    def _llamar_gemini_image():
        return client.models.generate_content(
            model=modelo,
            contents=prompt_completo,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
        )

    try:
        resultado = ejecutar_con_reintentos(
            _llamar_gemini_image,
            descripcion=f"Imagen Gemini ({modelo})",
            max_reintentos=2,
            espera_inicial=15,
            factor_escalonado=1.3
        )

        # Extraer imagen binaria desde los parts de la respuesta
        img_bytes = None
        if resultado and resultado.candidates:
            for candidate in resultado.candidates:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if part.inline_data and part.inline_data.data:
                            img_bytes = part.inline_data.data
                            break
                if img_bytes:
                    break

        if not img_bytes:
            raise RuntimeError(f"El modelo {modelo} respondió pero no devolvió datos de imagen.")

        img = Image.open(BytesIO(img_bytes))
        img.save(ruta_salida, format="PNG")
        print(f"[Imagen Gemini] Guardada con éxito en: {ruta_salida} ({img.width}x{img.height})")
        return ruta_salida

    except Exception as e:
        err_str = str(e)
        # Si la cuenta es Free Tier y Google tiene 'limit: 0' para generación de imágenes:
        if "limit: 0" in err_str or "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
            print(f"\n[Aviso Cuota de Imagen] Google reportó: {modelo} tiene 'limit: 0' en el plan gratuito de tu API Key.")
            print("  (Para habilitar imágenes nativas de Google, vincula facturación en Google AI Studio).")
            print("  Activando generador de respaldo FLUX (9:16 vertical gratis)...")
            return generar_imagen_fallback_flux(prompt_completo, ruta_salida)
        raise e

def generar_imagenes_desde_json(datos_json: dict, carpeta_salida: str = "assets") -> list:
    """
    Itera sobre las escenas del JSON y genera las imágenes en 'carpeta_salida/img_{id}.png'.
    Aplica una pausa de 5 segundos entre cada generación para respetar límites de cuota.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    client = obtener_cliente_imagen()
    estilo_global = datos_json.get("estilo_visual_global", "")
    escenas = datos_json.get("escenas", [])
    rutas_imagenes = []
    total_escenas = len(escenas)

    print(f"[Fase 4] Iniciando producción de {total_escenas} escenas verticales en '{carpeta_salida}'...")
    for idx, escena in enumerate(escenas, start=1):
        escena_id = escena.get("id_escena", escena.get("escena_id", idx))
        ruta = os.path.join(carpeta_salida, f"img_{escena_id}.png")
        generar_imagen_escena(
            prompt=escena["prompt_imagen"],
            ruta_salida=ruta,
            estilo_global=estilo_global,
            cliente=client
        )
        rutas_imagenes.append(ruta)

        # Pausa preventiva de 5 segundos entre escenas
        if idx < total_escenas:
            print(f"[Fase 4] Pausa de 5 segundos antes de generar la siguiente escena ({idx}/{total_escenas})...")
            time.sleep(5)

    print(f"[Fase 4] Todas las imágenes ({len(rutas_imagenes)}) fueron generadas correctamente.")
    return rutas_imagenes
