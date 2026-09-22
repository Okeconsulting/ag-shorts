import os
import sys
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Soporte dual para MoviePy v1.x y v2.x
try:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
except ImportError:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip

def obtener_fuente_subtitulos(tamano: int = 42) -> ImageFont.ImageFont:
    """Intenta cargar fuentes sans-serif gruesas disponibles en Windows."""
    for nombre_fuente in ["arialbd.ttf", "arial.ttf", "segoeui.ttf", "calibrib.ttf"]:
        try:
            return ImageFont.truetype(nombre_fuente, tamano)
        except Exception:
            continue
    return ImageFont.load_default()

def crear_overlay_subtitulo(texto: str, ancho_video: int = 1080) -> np.ndarray:
    """
    Genera una imagen RGBA transparente con el subtítulo formateado al estilo Shorts/TikTok:
    - Tipografía en negrita (amarillo vibrante con contorno negro pronunciado).
    - Contenedor tipo píldora oscura semi-transparente para 100% de legibilidad.
    - Ajuste automático de líneas (máximo 28-32 caracteres por línea).
    """
    if not texto or not texto.strip():
        return None

    lineas = textwrap.wrap(texto.strip(), width=28)
    if not lineas:
        return None

    fuente = obtener_fuente_subtitulos(42)
    alto_linea = 52
    padding_v = 18
    padding_h = 32
    alto_caja = len(lineas) * alto_linea + padding_v * 2

    img = Image.new("RGBA", (ancho_video, alto_caja + 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calcular ancho máximo del texto para la píldora de fondo
    try:
        max_ancho_texto = max(draw.textlength(l, font=fuente) for l in lineas)
    except Exception:
        max_ancho_texto = 700

    x0 = max(20, (ancho_video - max_ancho_texto) / 2 - padding_h)
    x1 = min(ancho_video - 20, (ancho_video + max_ancho_texto) / 2 + padding_h)
    y0 = 10
    y1 = y0 + alto_caja

    # Dibujar fondo píldora semi-transparente
    draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=18, fill=(0, 0, 0, 185))

    # Dibujar líneas de texto centradas con borde negro y texto amarillo
    for idx, linea in enumerate(lineas):
        y_texto = y0 + padding_v + idx * alto_linea
        draw.text(
            (ancho_video / 2, y_texto),
            linea,
            font=fuente,
            fill="#FFD700",       # Amarillo dorado viral
            anchor="ma",          # Centrado horizontalmente
            stroke_width=4,       # Borde negro grueso
            stroke_fill="#000000"
        )

    return np.array(img)

def renderizar_video_final(
    num_escenas: int,
    carpeta_imagenes: str = "assets",
    carpeta_audios: str = "assets",
    archivo_salida: str = "short_final.mp4",
    fps: int = 30,
    matriz_escenas: list = None
) -> str:
    """
    Ensambla imágenes y audios con mejoras cinemáticas:
    1. Efecto Ken Burns (zoom suave in/out) para eliminar lo estático.
    2. Subtítulos dinámicos de alto impacto quemados sobre el video.
    3. Formato vertical 9:16 (1080x1920) y sincronización con el audio de cada escena.
    """
    clips_de_escenas = []
    directorio_salida = os.path.dirname(archivo_salida)
    if directorio_salida:
        os.makedirs(directorio_salida, exist_ok=True)

    print(f"\n[Renderizado Pro] Iniciando ensamblaje de línea de tiempo:")
    print(f"  - Total de escenas: {num_escenas}")
    print(f"  - Efecto dinámico:  Ken Burns Zoom In/Out activo")
    print(f"  - Subtítulos:       Activos (Amarillo / Fondo píldora oscura)")

    for i in range(1, num_escenas + 1):
        ruta_img = os.path.join(carpeta_imagenes, f"img_{i}.png")
        ruta_audio = os.path.join(carpeta_audios, f"audio_{i}.mp3")

        # Validar archivos
        if not os.path.exists(ruta_img) or not os.path.exists(ruta_audio):
            print(f"[Renderizado] Advertencia: Faltan archivos para la escena {i} ({ruta_img} o {ruta_audio})")
            continue

        # 1. Cargar audio y obtener duración
        audio_clip = AudioFileClip(ruta_audio)
        duracion = max(1.0, audio_clip.duration)

        # 2. Cargar imagen base y redimensionar a 1080x1920
        img_clip = ImageClip(ruta_img)
        if hasattr(img_clip, "with_duration"):
            img_clip = img_clip.with_duration(duracion)
        else:
            img_clip = img_clip.set_duration(duracion)

        if hasattr(img_clip, "resized"):
            img_clip = img_clip.resized(new_size=(1080, 1920))
        else:
            img_clip = img_clip.resize(height=1920, width=1080)

        # 3. Efecto Ken Burns (Movimiento cinemático de cámara suave)
        # Alterna entre Zoom In (1.00 -> 1.05) y Zoom Out (1.05 -> 1.00)
        try:
            if i % 2 == 0:
                img_animada = img_clip.resized(lambda t: 1.0 + 0.05 * (t / duracion))
            else:
                img_animada = img_clip.resized(lambda t: 1.05 - 0.05 * (t / duracion))
            img_animada = img_animada.with_position("center")
        except Exception:
            img_animada = img_clip.with_position("center")

        capas_escena = [img_animada]

        # 4. Generar y superponer subtítulo de la escena
        texto_narracion = ""
        if matriz_escenas and i - 1 < len(matriz_escenas):
            texto_narracion = matriz_escenas[i - 1].get("narracion", "")

        if texto_narracion:
            np_subtitulo = crear_overlay_subtitulo(texto_narracion, ancho_video=1080)
            if np_subtitulo is not None:
                sub_clip = ImageClip(np_subtitulo, is_mask=False)
                if hasattr(sub_clip, "with_duration"):
                    sub_clip = sub_clip.with_duration(duracion).with_position(("center", 1360))
                else:
                    sub_clip = sub_clip.set_duration(duracion).set_pos(("center", 1360))
                capas_escenas_con_sub = capas_escena + [sub_clip]
                capas_escena = capas_escenas_con_sub

        # 5. Componer la escena completa con sus capas y audio
        try:
            escena_compuesta = CompositeVideoClip(capas_escena, size=(1080, 1920))
            if hasattr(escena_compuesta, "with_duration"):
                escena_compuesta = escena_compuesta.with_duration(duracion).with_audio(audio_clip)
            else:
                escena_compuesta = escena_compuesta.set_duration(duracion).set_audio(audio_clip)
        except Exception as e:
            print(f"[Renderizado] Fallback en composición de escena {i}: {e}")
            escena_compuesta = img_clip.with_audio(audio_clip)

        clips_de_escenas.append(escena_compuesta)
        print(f"[Renderizado] Escena {i}/{num_escenas} ensamblada con subtítulos ({duracion:.2f}s)")

    if not clips_de_escenas:
        raise RuntimeError(f"No se pudieron ensamblar clips. Verifica las carpetas '{carpeta_imagenes}' y '{carpeta_audios}'.")

    # 6. Concatenar todas las escenas
    print(f"\n[Renderizado] Concatenando {len(clips_de_escenas)} escenas...")
    video_final = concatenate_videoclips(clips_de_escenas, method="compose")

    # 7. Compilar archivo final
    print(f"[Renderizado] Compilando video final con audio y subtítulos en '{archivo_salida}'...")
    video_final.write_videofile(
        archivo_salida,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        threads=4
    )
    print(f"\n[Éxito Total] Video con subtítulos y dinamismo exportado en: {archivo_salida}")
    return archivo_salida
