import os

# Soporte dual para MoviePy v1.x y v2.x
try:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
except ImportError:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

def renderizar_video_final(num_escenas: int, archivo_salida: str = "short_final.mp4", fps: int = 30):
    """
    Ensambla imágenes y audios, ajustando la duración de cada escena 
    a la duración exacta de su pista de voz, y renderiza en hardware local.
    Compatible con MoviePy 1.x y 2.x en formato vertical 9:16 (1080x1920).
    """
    clips_de_video = []
    
    print("[Renderizado] Iniciando ensamblaje de línea de tiempo...")
    
    for i in range(1, num_escenas + 1):
        ruta_img = f"assets/img_{i}.png"
        ruta_audio = f"assets/audio_{i}.mp3"
        
        # Validar que los archivos existan
        if not os.path.exists(ruta_img) or not os.path.exists(ruta_audio):
            print(f"[Renderizado] Advertencia: Faltan archivos para la escena {i} ({ruta_img} o {ruta_audio})")
            continue
            
        # 1. Cargar el audio y obtener su duración exacta
        audio_clip = AudioFileClip(ruta_audio)
        duracion = audio_clip.duration
        
        # 2. Cargar imagen y redimensionar a formato vertical (9:16 - 1080x1920)
        img_clip = ImageClip(ruta_img)

        # Duración
        if hasattr(img_clip, "with_duration"):
            img_clip = img_clip.with_duration(duracion)
        else:
            img_clip = img_clip.set_duration(duracion)

        # Dimensiones 1080x1920 (9:16)
        if hasattr(img_clip, "resized"):
            img_clip = img_clip.resized(new_size=(1080, 1920))
        else:
            img_clip = img_clip.resize(height=1920, width=1080)

        # Asignar audio
        if hasattr(img_clip, "with_audio"):
            img_clip = img_clip.with_audio(audio_clip)
        else:
            img_clip = img_clip.set_audio(audio_clip)
        
        clips_de_video.append(img_clip)
        print(f"[Renderizado] Escena {i} ensamblada ({duracion:.2f}s)")
        
    if not clips_de_video:
        raise RuntimeError("No se pudieron ensamblar clips. Revisa que existan imágenes y audios en assets/")

    # 3. Concatenar todos los clips en orden
    video_final = concatenate_videoclips(clips_de_video, method="compose")
    
    # 4. Compilar usando CPU local
    print(f"[Renderizado] Compilando archivo {archivo_salida} a {fps} FPS...")
    video_final.write_videofile(
        archivo_salida, 
        fps=fps, 
        codec="libx264", 
        audio_codec="aac",
        threads=4 
    )
    print(f"[Éxito] Video generado correctamente en: {archivo_salida}")
    return archivo_salida
