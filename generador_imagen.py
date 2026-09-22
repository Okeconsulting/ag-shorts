import os
import sys
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

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

    resultado = client.models.generate_images(
        model=modelo,
        prompt=prompt_completo,
        config=config
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
    Retorna la lista de rutas generadas.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    client = obtener_cliente_imagen()
    estilo_global = datos_json.get("estilo_visual_global", "")
    escenas = datos_json.get("escenas", [])
    rutas_imagenes = []

    print(f"[Imagen 3] Iniciando generación de {len(escenas)} escenas verticales en '{carpeta_salida}'...")
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

    print(f"[Imagen 3] Todas las imágenes ({len(rutas_imagenes)}) fueron generadas correctamente.")
    return rutas_imagenes
