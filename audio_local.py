import os
import sys
import asyncio
import edge_tts
from dotenv import load_dotenv

load_dotenv()

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def compilar_audio(texto: str, ruta_salida: str, voz: str = "es-CL-LorenzoNeural"):
    """
    Genera un archivo MP3 a partir del texto mediante edge-tts.
    Voz principal: es-CL-LorenzoNeural.
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    comunicador = edge_tts.Communicate(texto, voz)
    await comunicador.save(ruta_salida)
    print(f"[Audio] Generado: {ruta_salida} con voz {voz}")

def generar_audios_desde_json(datos_json: dict, carpeta_salida: str = "assets", voz: str = None) -> list:
    """
    Genera los audios de todas las escenas descritas en el JSON dentro de 'carpeta_salida'.
    Retorna la lista de rutas a los audios generados.
    """
    voz_final = voz or os.getenv("TTS_VOICE", "es-CL-LorenzoNeural")
    os.makedirs(carpeta_salida, exist_ok=True)
    
    escenas = datos_json.get("escenas", [])
    rutas_audios = []
    
    print(f"[Audio] Sintetizando {len(escenas)} pistas con voz '{voz_final}' en '{carpeta_salida}'...")
    for idx, escena in enumerate(escenas, start=1):
        num_id = escena.get("id_escena", escena.get("escena_id", idx))
        ruta = os.path.join(carpeta_salida, f"audio_{num_id}.mp3")
        asyncio.run(compilar_audio(escena["narracion"], ruta, voz=voz_final))
        rutas_audios.append(ruta)
        
    print(f"[Audio] Todos los audios ({len(rutas_audios)}) fueron generados exitosamente.")
    return rutas_audios