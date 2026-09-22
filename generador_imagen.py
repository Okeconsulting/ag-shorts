import os
import sys
import time
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

def generar_imagen_escena(prompt: str, ruta_salida: str, estilo_global: str = "", cliente: genai.Client = None) -> str:
    """
    Genera una imagen en formato vertical 9:16 utilizando Google Imagen 3 y la guarda en la ruta indicada.
    Incluye reintentos automáticos si Google reporta alta demanda (503).
    """
    client = cliente or obtener_cliente_imagen()
    modelo = os.getenv("IMAGEN_MODEL", "imagen-3.0-generate-002")

    prompt_completo = prompt
    if estilo_global and estilo_global not in prompt:
        prompt_completo = f"{prompt}, visual style: {estilo_global}, high quality, 9:16 vertical orientation, no text"

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    print(f"[Imagen 3] Generando escena: '{prompt_completo[:60]}...'")

    config = types.GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio="9:16",
        output_mime_type="image/png"
    )

    def _llamar_imagen():
        return client.models.generate_images(
            model=modelo,
            prompt=prompt_completo,
            config=config
        )

    resultado = ejecutar_con_reintentos(
        _llamar_imagen,
        descripcion="Google Imagen 3",
        max_reintentos=3,
        espera_inicial=60,
        factor_escalonado=1.3
    )

    if not resultado.generated_images:
        raise RuntimeError(f"Google Imagen 3 no devolvió ninguna imagen para el prompt: {prompt}")

    img_data = resultado.generated_images[0].image.image_bytes
    img = Image.open(BytesIO(img_data))
    img.save(ruta_salida, format="PNG")
    print(f"[Imagen 3] Guardada con éxito en: {ruta_salida} ({img.width}x{img.height})")
    return ruta_salida

def generar_imagenes_desde_json(datos_json: dict, carpeta_salida: str = "assets") -> list:
    """
    Itera sobre las escenas del JSON y genera las imágenes en 'carpeta_salida/img_{id}.png'.
    Aplica una pausa de 5 segundos entre cada generación para evitar saturar la cuota de la API.
    Retorna la lista de rutas generadas.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    client = obtener_cliente_imagen()
    estilo_global = datos_json.get("estilo_visual_global", "")
    escenas = datos_json.get("escenas", [])
    rutas_imagenes = []
    total_escenas = len(escenas)

    print(f"[Imagen 3] Iniciando generación de {total_escenas} escenas verticales en '{carpeta_salida}'...")
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

        # Pausa preventiva de 5 segundos entre generaciones de imágenes para no saturar
        if idx < total_escenas:
            print(f"[Imagen 3] Pausa preventiva de 5 segundos antes de la siguiente escena ({idx}/{total_escenas})...")
            time.sleep(5)

    print(f"[Imagen 3] Todas las imágenes ({len(rutas_imagenes)}) fueron generadas correctamente.")
    return rutas_imagenes
