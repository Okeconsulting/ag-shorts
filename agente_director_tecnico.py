import os
import sys
import json
import argparse
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from google import genai
from google.genai import types
from utils import slugify, ejecutar_con_reintentos

load_dotenv()

class EscenaTecnica(BaseModel):
    id_escena: int = Field(
        description="Identificador numérico correlativo de la escena (1, 2, 3...)"
    )
    narracion: str = Field(
        description="Fragmento de la narración en español para locución en esta escena."
    )
    prompt_imagen: str = Field(
        description="Prompt en INGLÉS detallado para escena visual estática, iluminación cinematográfica, 9:16 vertical format, sin texto visible."
    )
    duracion_estimada_segundos: int = Field(
        description="Duración estimada de la escena (estrictamente entre 3 y 5 segundos)."
    )

class MatrizProduccion(BaseModel):
    titulo_video: str = Field(
        description="Título conciso del video"
    )
    escenas: List[EscenaTecnica] = Field(
        description="Lista de escenas secuenciales de 3 a 5 segundos sumando entre 60 y 70 segundos totales."
    )

def obtener_cliente_gemini() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "tu_api_key" in api_key:
        raise ValueError(
            "No se ha configurado una GEMINI_API_KEY válida en el archivo .env.\n"
            "Consulta INSTRUCCIONES_CONFIGURACION.md para configurar tu clave."
        )
    return genai.Client(api_key=api_key)

def generar_matriz_director_tecnico(
    titulo_video: str,
    narracion_aprobada: str,
    estilo_visual: Optional[str] = None,
    carpeta_json: str = "JSON_Pront"
) -> tuple[dict, str]:
    """
    Agente Director Técnico (Paso 3):
    Toma el guion aprobado y genera la matriz de producción en formato JSON estricto:
    - Escenas de 3 a 5 segundos (60-70 seg totales).
    - Narrador masculino sentado ante laptop en tomas clave y cierre.
    - Prompts en inglés para Google Imagen 3 (9:16 vertical format, sin texto visible).
    - Guarda el resultado en 'JSON_Pront/<titulo_video>.json'.
    """
    client = obtener_cliente_gemini()
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    instrucciones_sistema = f"""
Eres un orquestador de video técnico automatizado. Tu única función es recibir el guion aprobado y devolver una matriz de producción en formato JSON estricto.

GUION APROBADO:
Título: {titulo_video}
Texto Completo:
{narracion_aprobada}

Reglas Técnicas de Producción:
1. El campo 'narracion': Distribuye íntegramente el texto aprobado a lo largo de las escenas en orden secuencial. No omitas texto ni inventes frases que alteren el guion. La última escena debe conservar el cierre institucional.
2. El campo 'prompt_imagen': DEBE estar en INGLÉS. Describe una escena visual estática y fotorrealista. NUNCA pidas texto visible en la imagen (agrega 'no text, no letters'). Obliga a que sea vertical ('9:16 vertical format').
3. Duración: Divide el contenido en escenas de entre 3 y 5 segundos, para obtener un total de 60 a 70 segundos (aproximadamente 14 a 18 escenas cortas y dinámicas).
4. Coherencia visual: Todas las escenas deben compartir la misma atmósfera, paleta de color e iluminación cinematográfica.
5. Narrador masculino ante laptop:
   - Características visuales inmutables: 'A professional Hispanic/Latino man in his 30s with short dark neat hair, well-groomed beard, wearing a charcoal minimalist crewneck sweater, seated at a clean dark wooden desk in front of a modern glowing laptop'.
   - Debe aparecer en la escena 1 (gancho), en escenas de transición intermedias y en la escena final.
6. Transición a conceptos: Las escenas conceptuales (diagramas, analogías, servidores, flujos de datos) deben usar la misma iluminación suave y paleta de color para asegurar transiciones suaves y naturales.

Estilo visual complementario: {estilo_visual or 'Cinematográfico, hiperrealista, iluminación suave de estudio tech, 8k'}
"""

    def _llamar_director():
        return client.models.generate_content(
            model=modelo,
            contents=instrucciones_sistema,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MatrizProduccion,
                temperature=0.4,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
        )

    response = ejecutar_con_reintentos(
        _llamar_director,
        descripcion=f"Agente Director Técnico ({modelo})",
        max_reintentos=3,
        espera_inicial=60,
        factor_escalonado=1.3
    )

    datos = json.loads(response.text)
    datos["titulo_video"] = titulo_video

    # Guardar en la carpeta JSON_Pront
    os.makedirs(carpeta_json, exist_ok=True)
    slug = slugify(titulo_video)
    ruta_guardado = os.path.join(carpeta_json, f"{slug}.json")

    with open(ruta_guardado, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

    escenas = datos.get("escenas", [])
    duracion_total = sum(e.get("duracion_estimada_segundos", 4) for e in escenas)
    print(f"[Director Técnico] Matriz JSON guardada exitosamente en: '{ruta_guardado}'")
    print(f"  - Total de escenas: {len(escenas)}")
    print(f"  - Duración estimada: {duracion_total} segundos")

    return datos, ruta_guardado

def main():
    parser = argparse.ArgumentParser(description="Agente Director Técnico - Matriz JSON")
    parser.add_argument("-i", "--input", dest="tema", type=str, required=True, help="Tema o archivo de guion")
    args = parser.parse_args()

    # Ejemplo de ejecución directa
    guion_ejemplo = "¿Sabías que los modelos de lenguaje no tienen memoria a largo plazo? Ahí es donde entran las bases de datos vectoriales. Convierten la información en coordenadas matemáticas para encontrar respuestas al instante. En Okeconsulting estamos para acompañarte."
    datos, ruta = generar_matriz_director_tecnico(args.tema, guion_ejemplo)
    print(f"Archivo generado en: {ruta}")

if __name__ == "__main__":
    main()
