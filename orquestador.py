import os
import sys
import json
import argparse
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agente_director import generar_guion_director
from audio_local import generar_audios_desde_json
from generador_imagen import generar_imagenes_desde_json
from ensamble_ren import renderizar_video_final

load_dotenv()

# Guion de respaldo / prueba rápida sin llamada a API si se requiere depuración
PAYLOAD_EJEMPLO = {
    "tema": "Funcionamiento de una API en la vida cotidiana",
    "estilo_visual_global": "Cyberpunk isometric neon digital art, 8k, cinematic lighting",
    "escenas": [
        {
            "escena_id": 1,
            "narracion": "Imagina que estás en un restaurante. Tú eres el cliente y la cocina es el servidor.",
            "prompt_imagen": "A customer looking at a futuristic glowing holographic menu inside a stylish cyberpunk restaurant, 9:16 vertical orientation",
            "duracion_estimada": 4
        },
        {
            "escena_id": 2,
            "narracion": "El mesero que lleva tu orden y regresa con tu comida, es exactamente lo que hace una API.",
            "prompt_imagen": "A sleek humanoid robot waiter delivering glowing digital data packets on a tray, neon reflections, 9:16 vertical orientation",
            "duracion_estimada": 5
        },
        {
            "escena_id": 3,
            "narracion": "Conecta aplicaciones entre sí de forma invisible y al instante. ¡Síguenos para más tecnología!",
            "prompt_imagen": "Glowing fiber optic light streams connecting digital smartphones and cloud servers in a futuristic city, 9:16 vertical orientation",
            "duracion_estimada": 4
        }
    ]
}

def ejecutar_pipeline_completo(
    tema: str = None, 
    estilo_visual: str = None, 
    num_escenas: int = 3, 
    usar_ejemplo: bool = False,
    salida_video: str = None
):
    """
    Orquesta las 4 fases de creación del Short:
    1. Agente Director (Google Gemini): Generación del guion y prompts 9:16.
    2. Agente de Audio (Edge-TTS): Síntesis de voz en español para cada escena.
    3. Agente Visual (Google Imagen 3): Generación de imágenes verticales por escena.
    4. Ensamblaje y Render (MoviePy): Montaje sincronizado y compilación de video MP4.
    """
    archivo_salida = salida_video or os.getenv("VIDEO_OUTPUT", "short_final.mp4")
    
    print("\n" + "="*60)
    print("[MOTOR TEXT-TO-VIDEO] PIPELINE DE YOUTUBE SHORTS")
    print("="*60)
    
    # FASE 1: Obtención del Guion (Agente Director)
    if usar_ejemplo:
        print("[Fase 1] Usando guion de ejemplo local (Modo depuración)...")
        datos_guion = PAYLOAD_EJEMPLO
    else:
        tema_final = tema or "Cómo la inteligencia artificial está transformando el mundo"
        print(f"[Fase 1] Invocando Agente Director (Gemini) para: '{tema_final}'...")
        try:
            datos_guion = generar_guion_director(tema_final, estilo_visual=estilo_visual, num_escenas=num_escenas)
        except Exception as e:
            print(f"\n[Aviso] No se pudo conectar con la API de Gemini: {e}")
            print("[Aviso] Puedes configurar tu clave en el archivo .env o usar '--ejemplo' para probar con datos simulados.")
            return

    # Guardar copia del guion generado en assets para trazabilidad
    os.makedirs("assets", exist_ok=True)
    with open("assets/guion_activo.json", "w", encoding="utf-8") as f:
        json.dump(datos_guion, f, indent=2, ensure_ascii=False)
    print(f"[Fase 1] Guion guardado para referencia en 'assets/guion_activo.json'")

    total_escenas = len(datos_guion["escenas"])
    print(f"\n--- Iniciando Producción: {datos_guion['tema']} ({total_escenas} escenas) ---")

    # FASE 2: Síntesis de Audio (Edge-TTS Local)
    print("\n[Fase 2] Generando narraciones de voz con Edge-TTS...")
    generar_audios_desde_json(datos_guion)

    # FASE 3: Generación Visual (Google Imagen 3)
    print("\n[Fase 3] Generando imágenes verticales 9:16 con Google Imagen 3...")
    try:
        generar_imagenes_desde_json(datos_guion)
    except Exception as e:
        print(f"\n[Error en Fase 3] No se pudieron generar las imágenes con Imagen 3: {e}")
        print("[Aviso] Si estás probando sin API Key o sin cuota de Imagen 3, puedes colocar imágenes manualmente en 'assets/img_1.png', etc.")
        return

    # FASE 4: Ensamblaje y Renderizado Local (MoviePy)
    print(f"\n[Fase 4] Ensamblando video vertical y renderizando en hardware local...")
    fps = int(os.getenv("VIDEO_FPS", "30"))
    renderizar_video_final(total_escenas, archivo_salida=archivo_salida, fps=fps)

    print("\n" + "="*60)
    print(f"[COMPLETADO] Video generado exitosamente en: {archivo_salida}")
    print("="*60 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Orquestador de Video Shorts Automatizados")
    parser.add_argument("--tema", type=str, help="Tema o concepto del video Short", default=None)
    parser.add_argument("--estilo", type=str, help="Estilo visual (ej. cyberpunk, anime, realista)", default=None)
    parser.add_argument("--escenas", type=int, help="Número de escenas", default=3)
    parser.add_argument("--ejemplo", action="store_true", help="Usar guion de prueba predefinido")
    parser.add_argument("--salida", type=str, help="Nombre del archivo de video de salida", default=None)

    args = parser.parse_args()

    ejecutar_pipeline_completo(
        tema=args.tema,
        estilo_visual=args.estilo,
        num_escenas=args.escenas,
        usar_ejemplo=args.ejemplo,
        salida_video=args.salida
    )

if __name__ == "__main__":
    main()