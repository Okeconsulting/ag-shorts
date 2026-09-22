import asyncio
import os
import edge_tts

async def compilar_audio(texto: str, ruta_salida: str, voz: str = "es-MX-JorgeNeural"):
    """
    Genera un archivo MP3 a partir del texto mediante edge-tts.
    Voces habituales: es-MX-JorgeNeural (masculino), es-MX-DaliaNeural (femenino),
    es-ES-AlvaroNeural, es-ES-ElviraNeural.
    """
    comunicador = edge_tts.Communicate(texto, voz)
    await comunicador.save(ruta_salida)
    print(f"[Audio] Generado: {ruta_salida} con voz {voz}")

def generar_audios_desde_json(datos_json: dict, voz: str = None):
    """
    Genera los audios de todas las escenas descritas en el JSON.
    Crea la carpeta 'assets' si no existe.
    """
    voz_final = voz or os.getenv("TTS_VOICE", "es-MX-JorgeNeural")
    
    if not os.path.exists("assets"):
        os.makedirs("assets", exist_ok=True)
        
    print(f"[Audio] Sintetizando {len(datos_json['escenas'])} pistas con voz '{voz_final}'...")
    for escena in datos_json["escenas"]:
        ruta = f"assets/audio_{escena['escena_id']}.mp3"
        asyncio.run(compilar_audio(escena["narracion"], ruta, voz=voz_final))
    print("[Audio] Todos los audios fueron generados exitosamente.")