# Guía de Uso del Motor Text-to-Video (Okeconsulting)

Este proyecto implementa un motor automatizado de **Text-to-Video** para YouTube Shorts, Reels y TikTok en formato vertical (9:16). Utiliza la **API de Google Gemini** como agentes de redacción y dirección técnica, el motor **FLUX** para la generación visual en 9:16 (100% gratuito sin requerir API Key adicional), **Edge-TTS** para locución en español y **MoviePy** para ensamblaje local con subtítulos dinámicos y efecto cinemático Ken Burns.

---

## 🏗️ Flujo de Producción en 6 Pasos

```
1. Entrada del Tema (CLI)
   └── python orquestador.py -i "tema a investigar"
2. Agente de Redacción (Gemini)
   └── Redacta título y narración (150-170 palabras para duración ≥ 60s + cierre institucional)
   └── 🛑 Pausa de Aprobación Humana (Aprobar / Cambiar palabras / Editar / Regenerar)
   └── Guarda en: guiones/<slug>.md y .json
3. Agente Director Técnico (Gemini)
   └── Diseña escenas dinámicas (~2.5s por toma, 20-30 escenas configurables)
   └── Define tomas con Presentador Robot ante laptop holográfica y conceptos visuales en 9:16
   └── Guarda en: JSON_Pront/<slug>.json
4. Generador Visual (FLUX 9:16 Gratuito)
   └── Descarga las imágenes fotorrealistas en 1080x1920 (9:16) con pausa preventiva de 5s
   └── Guarda en: Escenas/<slug>/img_X.png
5. Síntesis de Voz (Edge-TTS)
   └── Genera las narraciones por escena con voz 'es-CL-LorenzoNeural'
   └── Guarda en: Audios/<slug>/audio_X.mp3
6. Ensamblador y Render (MoviePy + Pillow)
   └── Efecto Ken Burns (zoom suave in/out en cada escena)
   └── Subtítulos dinámicos virales (amarillo vibrante con borde negro sobre píldora oscura)
   └── Sincronización exacta en 1080x1920 (9:16)
   └── Guarda en: shorts/<slug>/<slug>.mp4
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
📊 LONGITUD: 156 palabras (objetivo 150-170 palabras, mínimo 60s)
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

### Ejemplo 2: Ajustar Número de Escenas Dinámicas
El sistema utiliza 24 escenas de forma predeterminada (~2.5 segundos por toma para máxima retención). Si deseas ajustar el número de escenas:
```powershell
python orquestador.py -i "Qué es la arquitectura de microservicios" --escenas 30
```

---

### Ejemplo 3: Generar y Revisar Solo el Guion
Si deseas redactar y guardar el guion en `guiones/` sin generar imágenes ni video:
```powershell
python orquestador.py -i "Qué es un ataque de Phishing" --solo-guion
```
*Salida:* `guiones/que_es_un_ataque_de_phishing.md` y `.json`.

---

### Ejemplo 4: Generar Guion y Matriz Técnica de Escenas
Si deseas avanzar hasta la matriz JSON técnica en `JSON_Pront/` para revisar los prompts visuales y tomas de cámara:
```powershell
python orquestador.py -i "Qué son las bases de datos vectoriales" --solo-json
```
*Salida:* `JSON_Pront/que_son_las_bases_de_datos_vectoriales.json`.

---

### Ejemplo 5: Ejecución Desatendida / Automática
Para pipelines automatizados donde no se requiera intervención humana:
```powershell
python orquestador.py -i "La regla 3-2-1 para copias de seguridad" --auto
```

---

### Ejemplo 6: Modo de Prueba Local (Sin llamadas a API)
Prueba todo el pipeline de ensamblaje, audio, subtítulos y video con datos locales:
```powershell
python orquestador.py --ejemplo
```

---

## 📁 Organización de Archivos de Salida

Cada video producido almacena sus recursos de forma ordenada usando su título como identificador:

```text
ag-shorts/
├── guiones/
│   ├── que_es_la_computacion_en_la_nube.md     # Guion en formato lectura (150-170 palabras)
│   └── que_es_la_computacion_en_la_nube.json   # Datos estructurados del guion
├── JSON_Pront/
│   └── que_es_la_computacion_en_la_nube.json   # Matriz técnica de escenas y prompts
├── Escenas/
│   └── que_es_la_computacion_en_la_nube/       # Imágenes 9:16 descargadas con FLUX
│       ├── img_1.png
│       ├── img_2.png
│       └── ...
├── Audios/
│   └── que_es_la_computacion_en_la_nube/       # Pistas MP3 de cada escena (Edge-TTS)
│       ├── audio_1.mp3
│       ├── audio_2.mp3
│       └── ...
└── shorts/
    └── que_es_la_computacion_en_la_nube/       # Video final con subtítulos y zoom dinámico
        └── que_es_la_computacion_en_la_nube.mp4
```

---

## 🛡️ Reglas de Producción Integradas

1. **Voz:** Narración en español con locución fluida `es-CL-LorenzoNeural` vía Edge-TTS.
2. **Cierre Institucional:** Todo video finaliza obligatoriamente con *"En Okeconsulting estamos para acompañarte."*
3. **Duración Garantizada (≥ 60s):** Guion calibrado estrictamente a **150–170 palabras** (a ~140 palabras por minuto produce entre 62 y 70 segundos netos).
4. **Avatar Robot Oficial:** En las tomas de anclaje (escena 1, anclas intermedias y cierre) aparece un robot humanoide futurista y amigable con visor LED cian ante una laptop holográfica (`A sleek, friendly, futuristic humanoid robot with expressive glowing cyan LED visor eyes, polished white ceramic and matte titanium chassis, seated at a modern minimalist tech workstation in front of an open glowing holographic laptop`).
5. **Subtítulos Virales Automáticos:** Se queman directamente sobre el video con tipografía sans-serif gruesa en color amarillo dorado (`#FFD700`), contorno negro y píldora oscura semi-transparente en el tercio inferior (`y ≈ 1360`), garantizando 100% de legibilidad sin depender de ImageMagick externo.
6. **Efecto Ken Burns (Cámara Dinámica):** Alterna suavemente entre Zoom In (`1.00 -> 1.05`) y Zoom Out (`1.05 -> 1.00`) para que ningún fotograma sea estático.
7. **Motor Visual FLUX:** Imágenes fotorrealistas en 1080x1920 (9:16 vertical), 100% gratuito sin cuotas de facturación ni claves de Google Imagen 3.
8. **Resiliencia ante saturación (503 UNAVAILABLE):**
   - Ante congestión temporal de Gemini, el sistema activa automáticamente **3 reintentos escalonados** con una pausa inicial de **60 segundos** (escalando a 78s y 100s).
   - En la descarga de imágenes FLUX, aplica una **pausa preventiva de 5 segundos** entre cada escena para no saturar los endpoints.
