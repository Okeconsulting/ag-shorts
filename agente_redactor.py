import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from google import genai
from google.genai import types
from utils import slugify, ejecutar_con_reintentos

load_dotenv()

FRASE_CIERRE_OBLIGATORIA = "En Okeconsulting estamos para acompañarte."

class RedaccionShort(BaseModel):
    tema: str = Field(description="Tema o concepto técnico investigado")
    titulo_video: str = Field(description="Título atractivo, conciso y directo para el video Short")
    discurso_completo: str = Field(
        description="Discurso total de narración en excelente español, educativo, empático y de no más de 120 palabras. Debe terminar exactamente con: 'En Okeconsulting estamos para acompañarte.'"
    )
    conteo_palabras: int = Field(description="Número exacto de palabras del discurso_completo")
    idea_analogia: str = Field(description="Breve descripción de la analogía cotidiana empleada")

def obtener_cliente_gemini() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "tu_api_key" in api_key:
        raise ValueError(
            "No se ha configurado una GEMINI_API_KEY válida en el archivo .env.\n"
            "Consulta INSTRUCCIONES_CONFIGURACION.md para configurar tu clave."
        )
    return genai.Client(api_key=api_key)

def redactar_guion_tecnico(tema: str, enfoque: Optional[str] = None) -> dict:
    """
    Agente de Estilo y Redacción:
    Investiga el tema técnico y genera título + narración educativa,
    respetuosa, en excelente español, ≤ 120 palabras y con el cierre institucional.
    """
    client = obtener_cliente_gemini()
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    prompt_instrucciones = f"""
Eres el Especialista en Redacción y Comunicación Técnica de Okeconsulting.
Tu misión es investigar y redactar la narración para un video corto (YouTube Short / Reel) sobre el tema solicitado.

NORMAS ESTRICTAS DE REDACCIÓN:
1. IDIOMA Y ESTILO:
   - Utiliza un español impecable, natural, fluido y gramaticalmente pulcro.
   - Puntuación estratégica (comas y pausas) pensada para síntesis de voz automática.
2. ENFOQUE EDUCATIVO Y RESPETUOSO:
   - Explica el tema técnico mediante una analogía sencilla o un caso práctico.
   - Tono cálido, pedagógico y accesible.
   - CRÍTICO: Jamás menosprecies ni subestimes al espectador. Prohibido usar expresiones como "es obvio", "como todos saben" o "es muy fácil". Todo espectador merece respeto y aprendizaje claro.
3. LÍMITE DE PALABRAS:
   - El discurso completo DEBE TENER 120 PALABRAS O MENOS en total.
   - Diseñado para que la locución a ritmo claro y pausado dure entre 45 y 55 segundos.
4. CIERRE OBLIGATORIO:
   - La última frase del discurso debe ser EXACTAMENTE: "{FRASE_CIERRE_OBLIGATORIA}" (sin omitir ni modificar una sola palabra).

Tema técnico: {tema}
Enfoque o contexto adicional: {enfoque or 'Divulgación tecnológica para público general y empresas'}
"""

    def _llamar_gemini():
        return client.models.generate_content(
            model=modelo,
            contents=prompt_instrucciones,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RedaccionShort,
                temperature=0.6,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )
        )

    response = ejecutar_con_reintentos(
        _llamar_gemini,
        descripcion=f"Agente Redactor ({modelo})",
        max_reintentos=3,
        espera_inicial=60,
        factor_escalonado=1.3
    )

    datos = json.loads(response.text)
    discurso = datos.get("discurso_completo", "").strip()

    # Asegurar frase de cierre
    if not discurso.endswith(FRASE_CIERRE_OBLIGATORIA):
        if FRASE_CIERRE_OBLIGATORIA in discurso:
            idx = discurso.rfind(FRASE_CIERRE_OBLIGATORIA)
            discurso = discurso[:idx + len(FRASE_CIERRE_OBLIGATORIA)].strip()
        else:
            discurso = f"{discurso.rstrip('.')} {FRASE_CIERRE_OBLIGATORIA}"

    # Límite estricto de 120 palabras
    palabras = discurso.split()
    if len(palabras) > 120:
        cierre_palabras = FRASE_CIERRE_OBLIGATORIA.split()
        cuerpo = palabras[:(120 - len(cierre_palabras))]
        discurso = " ".join(cuerpo).rstrip(".,;:") + ". " + FRASE_CIERRE_OBLIGATORIA

    datos["discurso_completo"] = discurso
    datos["conteo_palabras"] = len(discurso.split())

    return datos

def guardar_guion_aprobado(datos_guion: dict, carpeta_guiones: str = "guiones") -> str:
    """
    Guarda el guion aprobado en formato .md y .json dentro de la carpeta 'guiones/'.
    """
    os.makedirs(carpeta_guiones, exist_ok=True)
    slug = slugify(datos_guion.get("titulo_video", datos_guion.get("tema", "guion")))
    ruta_md = os.path.join(carpeta_guiones, f"{slug}.md")
    ruta_json = os.path.join(carpeta_guiones, f"{slug}.json")

    contenido_md = f"""# {datos_guion.get('titulo_video')}

- **Tema:** {datos_guion.get('tema')}
- **Palabras:** {datos_guion.get('conteo_palabras')} palabras (límite 120)
- **Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Analogía:** {datos_guion.get('idea_analogia')}

---

## 🎙️ Narración Completa

{datos_guion.get('discurso_completo')}
"""

    with open(ruta_md, "w", encoding="utf-8") as f:
        f.write(contenido_md)

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(datos_guion, f, indent=2, ensure_ascii=False)

    print(f"[Agente Redactor] Guion guardado exitosamente en:")
    print(f"  - Markdown: {ruta_md}")
    print(f"  - JSON:     {ruta_json}")
    return ruta_md

def solicitar_aprobacion_humana(datos_guion: dict, auto_aprobar: bool = False) -> Optional[dict]:
    """
    Presenta el guion en consola para aprobación humana interactiva.
    Permite: Aprobar [A], Cambiar palabras específicas [C], Editar todo el texto [E],
    Editar título [T], Regenerar [R], Cancelar [X].
    """
    guion_actual = dict(datos_guion)

    while True:
        titulo = guion_actual.get("titulo_video", "Sin título")
        discurso = guion_actual.get("discurso_completo", "")
        palabras = len(discurso.split())
        guion_actual["conteo_palabras"] = palabras

        print("\n" + "="*65)
        print("📝 PROPUESTA DEL AGENTE DE REDACCIÓN")
        print("="*65)
        print(f"📌 TÍTULO:   {titulo}")
        print(f"💡 ANALOGÍA: {guion_actual.get('idea_analogia')}")
        print(f"📊 LONGITUD: {palabras} palabras (máximo 120)")
        print("-"*65)
        print("🎙️ NARRACIÓN:")
        print(discurso)
        print("="*65)

        if auto_aprobar:
            print("[Aprobación] Modo automático activo: Guion aprobado.")
            break

        print("\nOpciones de Aprobación Humana:")
        print("  [A] Aprobar y continuar al Agente Director Técnico")
        print("  [C] Cambiar / reemplazar una palabra o frase específica")
        print("  [E] Editar manualmente toda la narración")
        print("  [T] Editar el título del video")
        print("  [R] Regenerar guion con Gemini (nuevo intento)")
        print("  [X] Cancelar proceso")

        opcion = input("\n👉 Selecciona una opción (A/C/E/T/R/X) [A]: ").strip().upper()
        if not opcion or opcion == "A":
            print("[Aprobación] ¡Guion aprobado por el usuario!")
            break

        elif opcion == "C":
            buscar = input("Texto/palabra que deseas reemplazar: ").strip()
            if not buscar:
                print("Operación cancelada: texto vacío.")
                continue
            if buscar not in discurso:
                print(f"No se encontró '{buscar}' en la narración actual.")
                continue
            reemplazo = input(f"Reemplazar '{buscar}' por: ").strip()
            nuevo_discurso = discurso.replace(buscar, reemplazo)
            if not nuevo_discurso.endswith(FRASE_CIERRE_OBLIGATORIA):
                nuevo_discurso = f"{nuevo_discurso.rstrip('.')} {FRASE_CIERRE_OBLIGATORIA}"
            guion_actual["discurso_completo"] = nuevo_discurso
            print("Texto actualizado con éxito.")

        elif opcion == "E":
            print("\nEscribe o pega la nueva narración completa:")
            nuevo_texto = input("> ").strip()
            if nuevo_texto:
                if not nuevo_texto.endswith(FRASE_CIERRE_OBLIGATORIA):
                    nuevo_texto = f"{nuevo_texto.rstrip('.')} {FRASE_CIERRE_OBLIGATORIA}"
                guion_actual["discurso_completo"] = nuevo_texto
                print("Narración editada correctamente.")

        elif opcion == "T":
            nuevo_titulo = input(f"Nuevo título [{titulo}]: ").strip()
            if nuevo_titulo:
                guion_actual["titulo_video"] = nuevo_titulo
                print("Título actualizado.")

        elif opcion == "R":
            enfoque_extra = input("Instrucción o enfoque para la regeneración (Enter para omitir): ").strip()
            tema = guion_actual.get("tema", "Tecnología")
            try:
                guion_actual = redactar_guion_tecnico(tema, enfoque=enfoque_extra or None)
            except Exception as e:
                print(f"Error al regenerar: {e}")

        elif opcion == "X":
            print("[Cancelado] Proceso detenido por el usuario.")
            return None
        else:
            print("Opción no válida. Por favor selecciona A, C, E, T, R o X.")

    # Guardar en la carpeta guiones
    guardar_guion_aprobado(guion_actual, carpeta_guiones="guiones")
    return guion_actual

def main():
    parser = argparse.ArgumentParser(description="Agente de Estilo y Redacción - Okeconsulting")
    parser.add_argument("-i", "--input", "--tema", dest="tema", type=str, required=True, help="Tema técnico a investigar")
    parser.add_argument("--auto", action="store_true", help="Aprobar automáticamente sin pausar")

    args = parser.parse_args()

    try:
        datos = redactar_guion_tecnico(args.tema)
        guion_final = solicitar_aprobacion_humana(datos, auto_aprobar=args.auto)
        if guion_final:
            print(f"\n[Listo] Guion final preparado para producción: '{guion_final.get('titulo_video')}'")
    except Exception as e:
        print(f"[Error] {e}")

if __name__ == "__main__":
    main()
