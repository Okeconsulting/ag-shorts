# ag-shorts

Este es la construcción de un motor de Text-to-Video automatizado. Utiliza la API de Gemini (o cualquier LLM compatible con salida JSON) como el Agente Director para la estructura, y delega el renderizado, síntesis de voz y ensamblaje a tu hardware local mediante Python.

## 🚀 Inicio Rápido

El punto de entrada del motor es `orquestador.py`:

```powershell
python orquestador.py -i "tema a investigar"
```

Para consultar la guía detallada de uso, opciones CLI y ejemplos completos, revisa [instruccion.md](instruccion.md).
