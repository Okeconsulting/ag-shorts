# Guía de Configuración y Gestión de Credenciales de Google

Esta guía explica cómo configurar tu API Key de Google (Gemini e Imagen 3), cómo cambiar entre diferentes cuentas de Google de forma segura y cómo mantener tus credenciales protegidas.

---

## 1. Obtención de la API Key en Google AI Studio

Para utilizar el **Agente Director (Gemini)** y el **Generador Visual (Google Imagen 3)** necesitas una API Key de Google AI Studio:

1. Ingresa a [Google AI Studio](https://aistudio.google.com/).
2. Inicia sesión con la cuenta de Google que tenga acceso a **Gemini Pro** o el plan que vayas a utilizar.
3. Haz clic en el botón azul **"Get API key"** (o "Obtener clave de API") en el menú lateral.
4. Selecciona **"Create API key in new project"** (o elige un proyecto existente de Google Cloud).
5. Copia la clave generada (empieza por `AIzaSy...`).

---

## 2. Configuración en el archivo `.env`

El proyecto utiliza variables de entorno mediante el paquete `python-dotenv`. El archivo `.env` contiene tus claves privadas y está protegido por `.gitignore` para que **nunca se suba a GitHub**.

1. Abre el archivo `.env` en la raíz del proyecto.
2. Pega tu clave en la variable `GEMINI_API_KEY`:
   ```bash
   GEMINI_API_KEY=AIzaSyTuClaveRealDeGoogleAqui
   ```
3. Verifica los modelos configurados:
   ```bash
   GEMINI_MODEL=gemini-2.5-flash
   IMAGEN_MODEL=imagen-3.0-generate-002
   TTS_VOICE=es-MX-JorgeNeural
   ```

---

## 3. Cómo cambiar entre diferentes cuentas de Google

Si trabajas con múltiples cuentas de Google (por ejemplo, cuenta personal, cuenta corporativa/pro, o cuentas con diferentes cuotas de facturación):

### Método A: Cambio directo en `.env` (Recomendado)
Simplemente genera la API Key en la otra cuenta de Google AI Studio y reemplaza el valor de `GEMINI_API_KEY` en tu archivo `.env`:
```bash
GEMINI_API_KEY=AIzaSyClaveDeLaSegundaCuenta
```

### Método B: Perfiles de entorno alternativos
Puedes tener varios archivos para cambiar rápidamente según el proyecto o la cuenta:
- `.env.personal`
- `.env.trabajo`

Para alternar, copia el archivo deseado a `.env`:
```powershell
# En PowerShell:
Copy-Item .env.trabajo .env -Force
```

---

## 4. Modelos Disponibles y Cuotas

### Modelos de Texto / Guion (Agente Director)
- **`gemini-2.5-flash`** (Recomendado): Muy rápido, excelente razonamiento y soporte nativo para esquemas JSON estructurados.
- **`gemini-1.5-pro`**: Ideal para guiones con narrativa compleja o investigación profunda.

### Modelos de Generación Visual (Imágenes)
- **`imagen-3.0-generate-002`**: Modelo de Google Imagen 3 de alta fidelidad, con soporte para formato vertical `9:16`.

> [!NOTE]
> Las cuentas gratuitas de Google AI Studio tienen límites de peticiones por minuto (RPM) y por día (RPD). Las cuentas con facturación vinculada (Tier 1 / Pay-as-you-go) permiten mayores volúmenes y acceso pleno a Imagen 3.

---

## 5. Seguridad de las Credenciales

- **Nunca compartas ni hagas commit de tu archivo `.env`**.
- El archivo `.gitignore` ya está configurado para ignorar `.env` y `.env.*.local`.
- Si sospechas que una clave fue expuesta, revócala de inmediato en la consola de [Google AI Studio API Keys](https://aistudio.google.com/app/apikey).
