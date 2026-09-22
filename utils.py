import re
import unicodedata

def slugify(texto: str, max_longitud: int = 50) -> str:
    """
    Convierte cualquier título o tema en un nombre de carpeta o archivo seguro para Windows/Linux.
    Ejemplo: '¿Cómo funciona una API?' -> 'como_funciona_una_api'
    """
    # Normalizar caracteres unicode (remover tildes y diacríticos)
    texto_norm = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    # Minúsculas y reemplazar no-alfanuméricos por guiones bajos
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', texto_norm.lower()).strip('_')
    # Limitar longitud para evitar rutas excesivas en Windows
    if len(slug) > max_longitud:
        slug = slug[:max_longitud].rstrip('_')
    return slug or "video_sin_titulo"
