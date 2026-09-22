import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

class EscenaShort(BaseModel):
    escena_id: int = Field(description="Identificador correlativo de la escena (1, 2, ...)")
    narracion: str = Field(description="Texto en español para ser locutado por TTS en esta escena. Debe ser conciso, con gancho y ritmo ágil.")
    prompt_imagen: str = Field(description="Prompt en inglés detallado para Google Imagen 3. Incluye descripción del sujeto, iluminación cinematográfica, paleta de colores y especificación de formato vertical 9:16.")
    duracion_estimada: int = Field(description="Duración aproximada en segundos (típicamente entre 3 y 6 segundos).")

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
    Agente Director: Diseña la narrativa del video short, dividiéndola en escenas,
    creando la locución en español y los prompts de imagen para Imagen 3 en inglés.
    """
    client = obtener_cliente_gemini()
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    prompt_sistema = f"""
Eres un Director Creativo y Guionista experto en videos virales para YouTube Shorts, TikTok e Instagram Reels.
Tu objetivo es transformar la siguiente temática en un guion estructurado para producción automatizada de video.

Reglas del Guion:
1. Cantidad de escenas: exactamente {num_escenas} escenas.
2. Formato: Cada escena debe estar concebida para video vertical 9:16 (Short).
3. Narración (Voz en off):
   - Redactada en español neutro, dinámica y con gancho desde la escena 1.
   - Oraciones claras y fluidas para síntesis de voz automática.
4. Prompts de Imagen (para Google Imagen 3):
   - Redactados en inglés de alta calidad.
   - Describe sujeto, entorno, iluminación (ej. cinematic rim lighting, volumetric fog, vibrant neon, photorealistic 8k).
   - Mantén la coherencia visual con el estilo global elegido.
   - Menciona 'vertical composition, 9:16 aspect ratio'.

Temática solicitada: {tema}
Estilo visual deseado: {estilo_visual or 'Cinematográfico, hiperrealista, iluminación dramática'}
"""

    print(f"[Agente Director] Diseñando guion para el tema: '{tema}' con modelo '{modelo}'...")

    response = client.models.generate_content(
        model=modelo,
        contents=prompt_sistema,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=GuionShort,
            temperature=0.7,
        )
    )

    datos = json.loads(response.text)
    print(f"[Agente Director] Guion generado con éxito: {len(datos['escenas'])} escenas.")
    return datos

if __name__ == "__main__":
    import sys
    tema_prueba = "Funcionamiento de una API en la vida cotidiana"
    if len(sys.argv) > 1:
        tema_prueba = " ".join(sys.argv[1:])
    try:
        resultado = generar_guion_director(tema_prueba)
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
