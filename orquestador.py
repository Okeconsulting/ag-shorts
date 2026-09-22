import os
import sys
import json
import argparse
from dotenv import load_dotenv

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from utils import slugify
from agente_redactor import redactar_guion_tecnico, solicitar_aprobacion_humana
from agente_director_tecnico import generar_matriz_director_tecnico
from generador_imagen import generar_imagenes_desde_json
from audio_local import generar_audios_desde_json
from ensamble_ren import renderizar_video_final

# Payload de respaldo para pruebas rápidas sin API Key
PAYLOAD_EJEMPLO = {
    "titulo_video": "Que es una API",
    "tema": "Funcionamiento de una API en la vida cotidiana",
    "discurso_completo": "Imagina que estás en un restaurante. Tú eres el cliente y la cocina es el servidor. El mesero que lleva tu orden y regresa con tu comida, es exactamente lo que hace una API. Conecta aplicaciones entre sí de forma segura y al instante. En Okeconsulting estamos para acompañarte.",
    "conteo_palabras": 48,
    "idea_analogia": "Un mesero que lleva pedidos entre el cliente y la cocina",
    "escenas": [
        {
            "id_escena": 1,
            "narracion": "¿Sabías cómo se comunican las aplicaciones que usas todos los días?",
            "prompt_imagen": "A modern tech room with soft blue neon lighting, a handsome professional Hispanic male in his 30s with short dark hair, seated at a desk in front of a sleek laptop, looking thoughtfully towards the camera, cinematic lighting, photorealistic 8k, no text, 9:16 vertical format",
            "duracion_estimada_segundos": 4
        },
        {
            "id_escena": 2,
            "narracion": "Imagina que estás en un restaurante. Tú eres el cliente y la cocina es el servidor.",
            "prompt_imagen": "A customer looking at a futuristic glowing holographic menu inside a stylish cyberpunk restaurant, 9:16 vertical orientation, no text",
            "duracion_estimada_segundos": 4
        },
        {
            "id_escena": 3,
            "narracion": "El mesero que lleva tu orden y regresa con tu comida, es exactamente lo que hace una API.",
            "prompt_imagen": "A sleek humanoid robot waiter delivering glowing digital data packets on a tray, neon reflections, 9:16 vertical orientation, no text",
            "duracion_estimada_segundos": 5
        },
        {
            "id_escena": 4,
            "narracion": "Conecta sistemas de forma invisible y segura. En Okeconsulting estamos para acompañarte.",
            "prompt_imagen": "The same professional Hispanic male in his 30s smiling confidently in front of his laptop, warm ambient lighting, 9:16 vertical format, no text",
            "duracion_estimada_segundos": 4
        }
    ]
}

def ejecutar_flujo_completo(
    tema: str,
    estilo_visual: str = None,
    auto_aprobar: bool = False,
    usar_ejemplo: bool = False,
    solo_guion: bool = False,
    solo_json: bool = False
):
    """
    Ejecuta el proceso end-to-end de 6 pasos para producción de Shorts:
    1. Entrada del tema.
    2. Agente de Redacción + Aprobación/Edición Humana -> guiones/<slug>.md
    3. Agente Director Técnico -> JSON_Pront/<slug>.json
    4. Generación de imágenes Google Imagen 3 -> Escenas/<slug>/img_X.png
    5. Síntesis de voz Edge-TTS (es-CL-LorenzoNeural) -> Audios/<slug>/audio_X.mp3
    6. Ensamblaje y Renderizado MoviePy -> shorts/<slug>/<slug>.mp4
    """
    print("\n" + "="*70)
    print("🎬 MOTOR TEXT-TO-VIDEO OKECONSULTING: PIPELINE DE 6 PASOS")
    print("="*70)

    # --------------------------------------------------------------------------
    # PASO 1: Validación del tema de entrada
    # --------------------------------------------------------------------------
    print(f"\n[Paso 1] Tema recibido para producción: '{tema}'")

    # --------------------------------------------------------------------------
    # PASO 2: Agente de Redacción + Aprobación Humana + Guardado en 'guiones/'
    # --------------------------------------------------------------------------
    print("\n[Paso 2] Invocando Agente de Redacción y Comunicación Técnica...")
    if usar_ejemplo:
        datos_redaccion = PAYLOAD_EJEMPLO
    else:
        try:
            datos_redaccion = redactar_guion_tecnico(tema)
        except Exception as e:
            print(f"[Error en Paso 2] {e}")
            print("[Aviso] Puedes usar '--ejemplo' para ejecutar el flujo de prueba con datos locales.")
            return

    guion_aprobado = solicitar_aprobacion_humana(datos_redaccion, auto_aprobar=auto_aprobar)
    if not guion_aprobado:
        print("[Fin] Flujo cancelado durante la revisión del guion.")
        return

    titulo_video = guion_aprobado.get("titulo_video", tema)
    slug = slugify(titulo_video)
    narracion_aprobada = guion_aprobado.get("discurso_completo", "")

    if solo_guion:
        print(f"\n[Paso 2 Completado] Opción '--solo-guion' activada. Deteniendo aquí.")
        return

    # --------------------------------------------------------------------------
    # PASO 3: Agente Director Técnico + Guardado en 'JSON_Pront/'
    # --------------------------------------------------------------------------
    print("\n[Paso 3] Invocando Agente Director Técnico para diseño de escenas...")
    if usar_ejemplo:
        matriz_json = PAYLOAD_EJEMPLO
        os.makedirs("JSON_Pront", exist_ok=True)
        ruta_json = os.path.join("JSON_Pront", f"{slug}.json")
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(matriz_json, f, indent=2, ensure_ascii=False)
        print(f"[Paso 3] Matriz JSON de prueba guardada en: '{ruta_json}'")
    else:
        try:
            matriz_json, ruta_json = generar_matriz_director_tecnico(
                titulo_video=titulo_video,
                narracion_aprobada=narracion_aprobada,
                estilo_visual=estilo_visual,
                carpeta_json="JSON_Pront"
            )
        except Exception as e:
            print(f"[Error en Paso 3] {e}")
            return

    if solo_json:
        print(f"\n[Paso 3 Completado] Opción '--solo-json' activada. Deteniendo aquí.")
        return

    total_escenas = len(matriz_json.get("escenas", []))

    # --------------------------------------------------------------------------
    # PASO 4: Generación Visual con Motor FLUX (9:16) -> Escenas/<slug>/
    # --------------------------------------------------------------------------
    carpeta_escenas = os.path.join("Escenas", slug)
    print(f"\n[Paso 4] Generando escenas visuales en '{carpeta_escenas}' con motor FLUX (9:16)...")
    try:
        generar_imagenes_desde_json(matriz_json, carpeta_salida=carpeta_escenas)
    except Exception as e:
        print(f"\n[Error en Paso 4] {e}")
        return

    # --------------------------------------------------------------------------
    # PASO 5: Generación de Audio con Edge-TTS -> Audios/<slug>/
    # --------------------------------------------------------------------------
    carpeta_audios = os.path.join("Audios", slug)
    print(f"\n[Paso 5] Generando audios de locución en '{carpeta_audios}' con Edge-TTS...")
    generar_audios_desde_json(matriz_json, carpeta_salida=carpeta_audios)

    # --------------------------------------------------------------------------
    # PASO 6: Ensamblaje y Renderizado Final -> shorts/<slug>/<slug>.mp4
    # --------------------------------------------------------------------------
    carpeta_shorts = os.path.join("shorts", slug)
    archivo_video_salida = os.path.join(carpeta_shorts, f"{slug}.mp4")
    print(f"\n[Paso 6] Ensamblando video final vertical en '{archivo_video_salida}'...")
    fps = int(os.getenv("VIDEO_FPS", "30"))

    renderizar_video_final(
        num_escenas=total_escenas,
        carpeta_imagenes=carpeta_escenas,
        carpeta_audios=carpeta_audios,
        archivo_salida=archivo_video_salida,
        fps=fps
    )

    print("\n" + "="*70)
    print(f"🎉 ¡PROCESO FINALIZADO EXITOSAMENTE!")
    print(f"  - Guion:  guiones/{slug}.md")
    print(f"  - Matriz: JSON_Pront/{slug}.json")
    print(f"  - Escenas: {carpeta_escenas}/")
    print(f"  - Audios:  {carpeta_audios}/")
    print(f"  - Video:   {archivo_video_salida}")
    print("="*70 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="Motor Text-to-Video de Okeconsulting - Flujo de 6 Pasos",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-i", "--input", "--tema", dest="tema", type=str, default=None,
                        help="Tema o concepto técnico a investigar (Paso 1)")
    parser.add_argument("--estilo", type=str, default=None,
                        help="Estilo visual adicional para Google Imagen 3")
    parser.add_argument("--auto", action="store_true",
                        help="Aprobar automáticamente el guion sin pedir confirmación por consola")
    parser.add_argument("--ejemplo", action="store_true",
                        help="Modo de prueba local con datos predefinidos")
    parser.add_argument("--solo-guion", action="store_true",
                        help="Detener el proceso tras el Paso 2 (guardar guion)")
    parser.add_argument("--solo-json", action="store_true",
                        help="Detener el proceso tras el Paso 3 (guardar matriz JSON)")

    args = parser.parse_args()

    tema_seleccionado = args.tema
    if not tema_seleccionado and not args.ejemplo:
        print("="*60)
        print("🎬 Bienvenido al Motor Text-to-Video de Okeconsulting")
        print("="*60)
        tema_seleccionado = input("👉 Ingresa el tema a investigar: ").strip()
        if not tema_seleccionado:
            print("[Error] Debes proporcionar un tema para iniciar la producción.")
            return

    ejecutar_flujo_completo(
        tema=tema_seleccionado or "Funcionamiento de una API",
        estilo_visual=args.estilo,
        auto_aprobar=args.auto,
        usar_ejemplo=args.ejemplo,
        solo_guion=args.solo_guion,
        solo_json=args.solo_json
    )

if __name__ == "__main__":
    main()