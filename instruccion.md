# Guía de Uso del Motor Text-to-Video (Okeconsulting)

Este proyecto implementa un motor automatizado de **Text-to-Video** para YouTube Shorts, Reels y TikTok en formato vertical (9:16). Utiliza la **API de Google Gemini** como agentes de redacción y dirección técnica, **Google Imagen 3** para la generación visual, **Edge-TTS** para locución en español y **MoviePy** para ensamblaje local.

---

## 🏗️ Flujo de Producción en 6 Pasos

```
1. Entrada del Tema (CLI)
   └── python orquestador.py -i "tema a investigar"
2. Agente de Redacción (Gemini)
   └── Redacta título y narración (≤ 120 palabras + cierre institucional)
   └── 🛑 Pausa de Aprobación Humana (Aprobar / Cambiar palabras / Editar / Regenerar)
   └── Guarda en: guiones/<titulo_video>.md y .json
3. Agente Director Técnico (Gemini)
   └── Diseña escenas de 3 a 5 seg (60-70 seg totales)
   └── Define tomas con narrador masculino ante laptop y conceptos visuales en 9:16
   └── Guarda en: JSON_Pront/<titulo_video>.json
4. Generador Visual (Google Imagen 3)
   └── Descarga las imágenes fotorrealistas en 9:16
   └── Guarda en: Escenas/<titulo_video>/img_X.png
5. Síntesis de Voz (Edge-TTS)
   └── Genera las narraciones con la voz 'es-CL-LorenzoNeural'
   └── Guarda en: Audios/<titulo_video>/audio_X.mp3
6. Ensamblador y Render (MoviePy)
   └── Sincroniza imágenes con duración exacta de audio en 1080x1920 (9:16)
   └── Guarda en: shorts/<titulo_video>/<titulo_video>.mp4
```

---

## ⚙️ Configuración Previa

1. **Instalar dependencias:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Configurar API Key en `.env`:**
   Copia `.env.example` a `.env` y coloca tu clave de Google AI Studio:
   ```bash
   GEMINI_API_KEY=AIzaSy...TuClaveAqui...
   GEMINI_MODEL=gemini-2.5-flash
   IMAGEN_MODEL=imagen-3.0-generate-002
   TTS_VOICE=es-CL-LorenzoNeural
   VIDEO_FPS=30
   ```

---

## 🚀 Ejemplos de Uso

El punto de entrada principal del sistema es **`orquestador.py`**.

### Ejemplo 1: Producción Completa Interactiva
Inicia el flujo indicando el tema a investigar:
```powershell
python orquestador.py -i "Cómo funciona la computación en la nube"
```

Durante el **Paso 2**, el sistema pausará y te presentará el guion:
```text
=================================================================
📝 PROPUESTA DEL AGENTE DE REDACCIÓN
=================================================================
📌 TÍTULO:   La nube explicada fácil
💡 ANALOGÍA: Alquilar una bodega digital en vez de comprar un galpón
📊 LONGITUD: 86 palabras (máximo 120)
-----------------------------------------------------------------
🎙️ NARRACIÓN:
¿Alguna vez te has preguntado dónde van tus fotos cuando las subes a internet?
...
En Okeconsulting estamos para acompañarte.
=================================================================

Opciones de Aprobación Humana:
  [A] Aprobar y continuar al Agente Director Técnico
  [C] Cambiar / reemplazar una palabra o frase específica
  [E] Editar manualmente toda la narración
  [T] Editar el título del video
  [R] Regenerar guion con Gemini (nuevo intento)
  [X] Cancelar proceso
```

- **Para cambiar una palabra:** Elige `[C]`, escribe la palabra a buscar y la palabra de reemplazo. El texto se actualizará inmediatamente sin reescribir todo.
- **Para aprobar:** Presiona `[A]` (o simplemente `Enter`).

---

### Ejemplo 2: Generar y Revisar Solo el Guion
Si deseas redactar y guardar el guion en `guiones/` sin generar imágenes ni video:
```powershell
python orquestador.py -i "Qué es un ataque de Phishing" --solo-guion
```
*Salida:* `guiones/que_es_un_ataque_de_phishing.md` y `.json`.

---

### Ejemplo 3: Generar Guion y Matriz Técnica de Escenas
Si deseas avanzar hasta la matriz JSON técnica en `JSON_Pront/` para revisar los prompts visuales de Imagen 3:
```powershell
python orquestador.py -i "Qué son las bases de datos vectoriales" --solo-json
```
*Salida:* `JSON_Pront/que_son_las_bases_de_datos_vectoriales.json`.

---

### Ejemplo 4: Ejecución Desatendida / Automática
Para pipelines automatizados donde no se requiera intervención humana:
```powershell
python orquestador.py -i "La regla 3-2-1 para copias de seguridad" --auto
```

---

### Ejemplo 5: Modo de Prueba Local (Sin llamadas a API)
Prueba todo el pipeline de ensamblaje, audio y video con datos locales sin consumir cuota:
```powershell
python orquestador.py --ejemplo
```

---

## 📁 Organización de Archivos de Salida

Cada video producido almacena sus recursos de forma ordenada usando su título como identificador:

```text
ag-shorts/
├── guiones/
│   ├── que_es_la_computacion_en_la_nube.md     # Guion en formato lectura
│   └── que_es_la_computacion_en_la_nube.json   # Datos estructurados del guion
├── JSON_Pront/
│   └── que_es_la_computacion_en_la_nube.json   # Matriz técnica de escenas y prompts
├── Escenas/
│   └── que_es_la_computacion_en_la_nube/       # Imágenes 9:16 descargadas
│       ├── img_1.png
│       ├── img_2.png
│       └── ...
├── Audios/
│   └── que_es_la_computacion_en_la_nube/       # Pistas MP3 de cada escena
│       ├── audio_1.mp3
│       ├── audio_2.mp3
│       └── ...
└── shorts/
    └── que_es_la_computacion_en_la_nube/       # Video final renderizado en 1080x1920
        └── que_es_la_computacion_en_la_nube.mp4
```

---

## 🛡️ Reglas de Producción Integradas

1. **Voz:** Narración en español neutro con voz `es-CL-LorenzoNeural` vía Edge-TTS.
2. **Cierre Institucional:** Todo video finaliza obligatoriamente con *"En Okeconsulting estamos para acompañarte."*
3. **Tiempo:** Discurso de máximo 120 palabras; escenas de 3 a 5 segundos con duración acumulada de 60 a 70 segundos.
4. **Coherencia Visual:** Narrador masculino ante laptop (*Hispanic/Latino man in his 30s seated in front of laptop*) en escenas de anclaje, intercalado con conceptos fotorrealistas sin texto visible en formato vertical 9:16.
