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
    duracion_estimada_segundos: float = Field(
        description="Duración estimada de la escena en segundos (ej. 2 a 4 segundos)."
    )

class MatrizProduccion(BaseModel):
    titulo_video: str = Field(
        description="Título conciso del video"
    )
    escenas: List[EscenaTecnica] = Field(
        description="Lista de escenas secuenciales sumando entre 60 y 70 segundos totales."
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
    num_escenas: int = 24,
    estilo_visual: Optional[str] = None,
    carpeta_json: str = "JSON_Pront"
) -> tuple[dict, str]:
    """
    Agente Director Técnico (Paso 3):
    Toma el guion aprobado y genera la matriz de producción en formato JSON estricto:
    - Escenas dinámicas (ritmo ágil, 60-70 seg totales).
    - Escena 1 y Escena Final usan la imagen oficial del Avatar de Marca (avatar/avatar.jpg).
    - Escenas intermedias en estética limpia, profesional y luminosa en TONOS CLAROS orientadas a Pymes.
    - Prompts en inglés para formato vertical 9:16 sin texto visible.
    - Guarda el resultado en 'JSON_Pront/<titulo_video>.json'.
    """
    client = obtener_cliente_gemini()
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    duracion_promedio = max(1.0, round(65.0 / max(1, num_escenas), 1))

    instrucciones_sistema = f"""
Eres un orquestador de video técnico automatizado para Okeconsulting. Tu única función es recibir el guion aprobado y devolver una matriz de producción en formato JSON estricto.

GUION APROBADO:
Título: {titulo_video}
Texto Completo:
{narracion_aprobada}

Reglas Técnicas de Producción:
1. El campo 'narracion': Distribuye íntegramente el texto aprobado a lo largo de las escenas en orden secuencial. No omitas texto ni inventes frases que alteren el guion. La última escena debe conservar exactamente el cierre institucional: 'En Okeconsulting estamos para acompañarte.'
2. El campo 'prompt_imagen': DEBE estar en INGLÉS. Describe una escena visual estática, fotorrealista o digital 3D limpia. NUNCA pidas texto visible en la imagen (agrega siempre 'no text, no letters'). Obliga a que sea vertical ('9:16 vertical format').
3. Duración y Dinamismo Visual: Divide el contenido en aproximadamente {num_escenas} escenas de ritmo muy ágil (promedio ~{duracion_promedio} segundos cada una), sumando un total estricto de entre 60 y 70 segundos netos para garantizar un ritmo dinámico y de alta retención.
4. ESTILO VISUAL OBLIGATORIO: TONOS CLAROS (BRIGHT LIGHT TONES):
   - Todas las imágenes DEBEN mantener una paleta luminosa en TONOS CLAROS: fondos blancos o beige suave, madera clara, luz natural de día, estética corporativa moderna, minimalista y optimista ('bright light tones, clean modern aesthetic, soft natural daylight, warm light wood, white walls, soft shadows, 8k render, no dark gloomy scenes, no text, no letters').
   - Prohibido utilizar fondos oscuros, neones nocturnos, atmósferas lúgubres o cyberpunk oscuro.
5. ESCENA 1 (INTRO) Y ESCENA FINAL (CIERRE) - AVATAR OFICIAL OKECONSULTING:
   - La primera escena (gancho) y la última escena (despedida institucional) corresponden a la imagen oficial del Avatar de Okeconsulting (un personaje elegante con traje café, corbata, cabeza circular blanca minimalista con gafas redondas, sentado ante una laptop en un escritorio de madera clara, en una oficina moderna y luminosa).
   - En el prompt de la escena 1 describe la introducción con este personaje en su oficina luminosa mirando hacia el espectador.
   - En el prompt de la última escena describe el cierre cálido con este mismo personaje en su oficina luminosa transmitiendo confianza y acompañamiento.
6. ESCENAS INTERMEDIAS (2 a N-1) - CONCEPTOS Y ANALOGÍAS PARA PYMES:
   - Ilustran de forma didáctica para dueños de Pymes los conceptos del guion (ej. flujos de trabajo organizados, dashboards limpios de métricas, conexiones automáticas entre tienda y pasarela de pago, inventarios sincronizados, personas de negocios en oficinas limpias y luminosas).
   - Siempre compartiendo la misma atmósfera luminosa en tonos claros para una coherencia visual impecable.

Estilo visual complementario: {estilo_visual or 'Tonos claros, iluminación natural de oficina moderna, maderas claras, estética limpia y luminosa, 8k render, no text'}
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
