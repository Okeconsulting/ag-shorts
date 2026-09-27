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
        description="Prompt en INGLÉS detallado. CRÍTICO: el sujeto y acción concreta de la narración DEBEN ir al inicio (primeras 10 palabras)."
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
    - Storyboarding LITERAL: cada escena ilustra de forma directa y tangible lo que dice la narración.
    - Sujeto y acción obligatorios en las primeras 10 palabras del prompt en inglés.
    - Escena 1 y Escena Final usan la imagen oficial del Avatar de Marca (avatar/avatar.jpg).
    - Escenas intermedias en estética 3D corporativa estilizada y limpia en TONOS CLAROS.
    - Guarda el resultado en 'JSON_Pront/<titulo_video>.json'.
    """
    client = obtener_cliente_gemini()
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    duracion_promedio = max(1.0, round(65.0 / max(1, num_escenas), 1))

    instrucciones_sistema = f"""
Eres un orquestador y director de arte de video técnico para Okeconsulting. Tu misión es transformar el guion aprobado en una matriz de producción JSON donde cada escena visual represente DE FORMA LITERAL, CLARA Y CONCRETA lo que se está narrando.

GUION APROBADO:
Título: {titulo_video}
Texto Completo:
{narracion_aprobada}

REGLAS ESTRICTAS DE STORYBOARDING Y DIRECCIÓN TÉCNICA:

1. CORRESPONDENCIA VISUAL LITERAL CON LA NARRACIÓN (CRÍTICO):
   - La imagen DEBE mostrar exactamente la acción, sujeto o analogía que se menciona en el campo 'narracion' de ESA escena específica.
   - PROHIBIDO USAR METÁFORAS ABSTRACTAS O REPETITIVAS: Está estrictamente prohibido poner "engranajes 3D", "relojes de arena mágicos", "escudos flotantes", "paredes vacías" o "gráficos abstractos" a menos que el guion hable explícitamente de eso.
   - Cada escena debe representar la acción real:
     * Si la narración habla de mensajes acumulados o clientes esperando fuera de horario -> Muestra un smartphone o pantalla en primer plano con burbujas de chats acumuladas y un comerciante revisando los mensajes.
     * Si habla de una tienda física abierta 24/7 -> Muestra la fachada o mostrador acogedor de una tienda o local comercial moderno con luz cálida y puertas abiertas recibiendo clientes.
     * Si habla de respuestas automáticas con IA -> Muestra una conversación de chat amigable en pantalla resolviendo una consulta de pedido al instante.
     * Si habla de pedidos recurrentes o envíos -> Muestra paquetes de compras organizados para despacho en un negocio limpio.
     * Si habla de ahorro de tiempo o tranquilidad del dueño -> Muestra al dueño o dueña de la Pyme sonriendo relajado al ver su negocio funcionando ordenadamente.

2. ESTRUCTURA OBLIGATORIA DE 'prompt_imagen' (SUJETO Y ACCIÓN AL INICIO):
   - DEBE estar en INGLÉS.
   - EL SUJETO Y LA ACCIÓN CONCRETA DEBEN IR EN LAS PRIMERAS 10 PALABRAS (los generadores de imagen priorizan el inicio del prompt).
   - NUNCA inicies el prompt con palabras de estilo como "Clean minimalist 3D...". Inicia SIEMPRE con el sujeto y la acción: "A smartphone screen held in hand showing...", "A bright modern boutique storefront...", "Neatly arranged delivery boxes...".
   - Formato obligatorio del prompt:
     "[Sujeto específico y acción concreta que ilustra la narración], [entorno de negocio o tienda en tonos claros y luz de día], clean minimalist 3D stylized render, elegant Pixar and Apple aesthetics, bright soft daylight, luminous light tones, ultra sharp focus, crisp fine details, 8k, 9:16 vertical format, no text, no letters, no blur"

3. ESCENA 1 (INTRO) Y ESCENA FINAL (CIERRE) - AVATAR DE MARCA:
   - La Escena 1 y la última escena corresponden a la imagen oficial del Avatar de Okeconsulting (personaje corporativo con traje café, corbata, cabeza circular blanca minimalista con gafas redondas, ante laptop en escritorio de madera clara, en oficina moderna y luminosa con logo de Okeconsulting).
   - En Escena 1: Describe al avatar introduciendo el tema mirando a cámara en su oficina luminosa.
   - En la Escena Final: Describe al avatar sonriendo cordialmente y cerrando con el acompañamiento de Okeconsulting.

4. ESCENAS INTERMEDIAS (2 a N-1) - VARIEDAD VISUAL COHERENTE:
   - Cada escena intermedia debe tener un sujeto visual DIFERENTE y CONCRETO que haga avanzar la historia de forma dinámica.
   - Todas comparten la misma estética (3D minimalista estilizado, tonos claros, luz diurna, ultra sharp focus) pero con SUJETOS VARIADOS Y DIRECTAMENTE RELACIONADOS AL GUION.

5. DURACIÓN Y DISTRIBUCIÓN:
   - Divide el contenido en aproximadamente {num_escenas} escenas ágiles (promedio ~{duracion_promedio} segundos cada una), sumando entre 60 y 70 segundos totales.
   - Distribuye la narración en orden secuencial sin omitir texto.
   - La última escena debe terminar exactamente con: 'En Okeconsulting estamos para acompañarte.'

Estilo visual complementario: {estilo_visual or 'Clean minimalist 3D stylized render, bright light tones, soft natural daylight, ultra sharp focus, 8k render, no text, no blur'}
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
