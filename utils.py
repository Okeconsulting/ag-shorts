import re
import time
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

def ejecutar_con_reintentos(
    operacion_func,
    descripcion: str = "Petición a Google API",
    max_reintentos: int = 3,
    espera_inicial: int = 60,
    factor_escalonado: float = 1.3
):
    """
    Ejecuta una llamada a la API de Google con 3 reintentos espaciados y escalonados
    ante errores 503 UNAVAILABLE (alta demanda temporal) o límites de cuota (429).
    Espera inicialmente 60 segundos y aumenta el tiempo progresivamente.
    """
    espera = espera_inicial
    for intento in range(1, max_reintentos + 1):
        try:
            return operacion_func()
        except Exception as e:
            err_str = str(e)
            es_saturacion = (
                "503" in err_str
                or "UNAVAILABLE" in err_str.upper()
                or "high demand" in err_str.lower()
                or "RESOURCE_EXHAUSTED" in err_str.upper()
                or "429" in err_str
            )
            if not es_saturacion or intento == max_reintentos:
                raise e

            print(f"\n" + "!"*65)
            print(f"[Aviso 503 - Alta Demanda en {descripcion}]")
            print(f"El servidor de Google reporta saturación temporal.")
            print(f"Pausa de {int(espera)} segundos antes del reintento {intento}/{max_reintentos}...")
            print("!"*65)

            # Progreso de espera en intervalos de 15 segundos
            tiempo_restante = int(espera)
            while tiempo_restante > 0:
                paso = min(15, tiempo_restante)
                time.sleep(paso)
                tiempo_restante -= paso
                if tiempo_restante > 0:
                    print(f"  ... esperando ({tiempo_restante}s restantes)...")

            print(f"Ejecutando reintento {intento + 1}/{max_reintentos + 1} para {descripcion}...\n")
            espera = int(espera * factor_escalonado)
