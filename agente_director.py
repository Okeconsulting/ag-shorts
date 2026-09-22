import os
import sys
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from google import genai
from google.genai import types

from agente_redactor import redactar_guion_tecnico, FRASE_CIERRE_OBLIGATORIA

load_dotenv()

class EscenaShort(BaseModel):
    escena_id: int = Field(description="Identificador correlativo de la escena (1, 2, ...)")
    narracion: str = Field(description="Fragmento de narración para esta escena.")
    prompt_imagen: str = Field(description="Prompt en inglés detallado para Google Imagen 3 en formato vertical 9:16.")
    duracion_estimada: int = Field(description="Duración aproximada en segundos para la escena.")

class GuionShort(BaseModel):
    tema: str = Field(description="Título o temática central del short")
    estilo_visual_global: str = Field(description="Directiva de estilo visual unificado para mantener consistencia en todas las imágenes")
    escenas: List[EscenaShort] = Field(description="Lista de escenas secuenciales para el video")

def obtener_cliente_gemini() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "tu_api_key" in api_key:
        raise ValueError(
            "No se ha configurado una GEMINI_API_KEY válida en el archivo .env.\n"
            "Consulta INSTRUCCIONES_CONFIGURACION.md para obtener y configurar tu clave."
        )
    return genai.Client(api_key=api_key)

def generar_guion_director(tema: str, estilo_visual: Optional[str] = None, num_escenas: int = 4) -> dict:
    """
    Agente Director:
    1. Llama al Agente de Estilo y Redacción para obtener el discurso (≤120 palabras, educativo y con cierre).
    2. Divide la narración en las escenas solicitadas.
    3. Diseña los prompts visuales en formato vertical 9:16 para Google Imagen 3 con coherencia estética.
    """
    # Paso 1: Redacción con el Agente de Estilo
    redaccion = redactar_guion_tecnico(tema)
    discurso_base = redaccion["discurso_completo"]

    client = obtener_cliente_gemini()
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Paso 2: Dirección técnica y división en escenas
    prompt_direccion = f"""
Eres el Director Visual y Técnico de producción para YouTube Shorts de Okeconsulting.
Tienes el siguiente discurso redactado por nuestro Agente de Redacción (máximo 120 palabras en total):

--- DISCURSO COMPLETO ---
{discurso_base}
-------------------------

Tu tarea es:
1. Dividir este discurso exactamente en {num_escenas} escenas secuenciales para locución.
   - El texto combinado de todas las escenas debe reproducir íntegramente el discurso, sin inventar texto nuevo ni alterar el mensaje.
   - La última escena DEBE culminar con la frase: "{FRASE_CIERRE_OBLIGATORIA}".
2. Para cada escena, redactar un 'prompt_imagen' profesional en INGLÉS optimizado para Google Imagen 3:
   - Formato y composición: 'vertical composition, 9:16 aspect ratio'.
   - Describe sujeto, entorno, iluminación (ej. cinematic soft lighting, volumetric atmosphere, 8k render).
   - Mantén una coherencia visual impecable con el estilo general.

Tema: {tema}
Estilo visual global: {estilo_visual or 'Cinematográfico, realista, iluminación elegante y profesional'}
"""

    print(f"[Agente Director] Diseñando storyboard visual de {num_escenas} escenas con '{modelo}'...")

    response = client.models.generate_content(
        model=modelo,
        contents=prompt_direccion,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GuionShort,
            temperature=0.4,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
    )

    datos = json.loads(response.text)

    # Validar que la última escena conserve el cierre
    if datos.get("escenas"):
        ultima_escena = datos["escenas"][-1]
        if not ultima_escena["narracion"].strip().endswith(FRASE_CIERRE_OBLIGATORIA):
            ultima_escena["narracion"] = f"{ultima_escena['narracion'].rstrip('.')} {FRASE_CIERRE_OBLIGATORIA}"

    print(f"[Agente Director] Storyboard completado con {len(datos['escenas'])} escenas.")
    return datos

if __name__ == "__main__":
    tema_prueba = "Qué es la computación en la nube"
    if len(sys.argv) > 1:
        tema_prueba = " ".join(sys.argv[1:])
    try:
        resultado = generar_guion_director(tema_prueba)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
