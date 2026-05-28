# Optimizador de CV con Inteligencia Artificial 🚀
### *Herramienta de Ingeniería de Perfil Profesional para Ingenieros Junior y Trainees*

Este proyecto es una plataforma y plantilla de andamiaje lista para producción diseñada con fines académicos y prácticos. Permite a los ingenieros junior y trainees optimizar sus currículums de forma automatizada y estructurada para ofertas laborales específicas utilizando el nuevo **Google GenAI SDK** y el modelo de última generación **Gemini 2.5 Flash**.

---

## 🎓 Objetivo Educativo

El objetivo de este proyecto es doble:
1. **Pedagógico / Técnico:** Introducir a ingenieros junior y trainees al desarrollo de aplicaciones impulsadas por modelos de lenguaje masivos (LLMs), aprendiendo a implementar **Structured Outputs** (salidas estructuradas de datos mediante Pydantic), el manejo seguro de archivos de configuración serializados (YAML), la integración de variables de entorno robustas (.env) y la automatización de la exportación a múltiples formatos de salida (Markdown y HTML con CSS adaptado a A4).
2. **Desarrollo Profesional:** Capacitar al ingeniero junior para presentar su perfil real con el máximo impacto técnico posible a través del **Efecto Pygmalion** (potenciación y empoderamiento de logros académicos y laborales reales) y alineación semántica con palabras clave del sector de ingeniería, **sin falsificar datos ni crear experiencia ficticia**.

---

## 🛠️ Requisitos Previos

Antes de comenzar, asegúrate de contar con lo siguiente:

1. **Python 3.10 o superior** instalado en tu sistema. Puedes comprobarlo ejecutando:
   ```bash
   python3 --version
   ```
2. **Una clave de API (API Key) gratuita de Gemini:**
   - Dirígete a [Google AI Studio](https://aistudio.google.com/).
   - Inicia sesión con tu cuenta de Google.
   - Haz clic en **"Get API key"** (Obtener clave de API).
   - Genera una clave nueva y cópiala de forma segura. *La API de Gemini en AI Studio ofrece una cuota gratuita ideal para desarrollo y experimentación académica.* Puedes consultar la guía completa en [GEMINI_API_KEY_GUIDE.md](GEMINI_API_KEY_GUIDE.md).

---

## 📁 Estructura del Proyecto

El proyecto está organizado bajo los más altos estándares de calidad y modularidad en Python:

```
cvgen/
├── config/
│   └── student_profile.yaml   # Archivo de configuración del perfil del ingeniero junior
├── templates/
│   └── cv_template.html       # Plantilla HTML Jinja2 editable para el diseño del CV
├── src/
│   ├── cv_optimizer.py        # Código fuente del optimizador principal de CV
│   └── test_cv_optimizer.py   # Suite de pruebas unitarias locales (unittest)
├── output/                    # Carpeta de salida (ignora los archivos generados en git)
│   └── .gitkeep               # Asegura la persistencia de la carpeta en Git
├── requirements.txt           # Definición de dependencias y librerías necesarias
├── .env.example               # Plantilla para tus variables de entorno locales
├── .gitignore                 # Configuración de archivos excluidos en Git
├── GEMINI_API_KEY_GUIDE.md    # Guía detallada en español para configurar tu API Key
└── README.md                  # Esta guía educativa y de usuario
```

---

## 🚀 Instalación y Configuración

Sigue estos sencillos pasos para configurar y ejecutar el proyecto localmente:

### Paso 1: Configurar el Entorno Virtual de Python
Se recomienda crear un entorno virtual limpio para no interferir con otras dependencias en tu sistema.

En macOS o Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### Paso 2: Instalar Dependencias
Instala todas las librerías necesarias (incluyendo **Jinja2** para la gestión de plantillas HTML) ejecutando el siguiente comando:
```bash
pip install -r requirements.txt
```

### Paso 3: Configurar tus Variables de Entorno
Crea un archivo llamado `.env` en la raíz del proyecto. Agrega la siguiente línea al archivo `.env`:

```env
GEMINI_API_KEY=tu_clave_de_api_secreta_aqui
```

*Importante: Nunca subas tu archivo `.env` o tu clave de API a repositorios públicos de GitHub. El archivo `.gitignore` configurado de fábrica ya evita que esto ocurra.*

---

## ✍️ Configuración del Perfil del Ingeniero Junior

El optimizador utiliza el archivo `config/student_profile.yaml` como la única base de datos real del ingeniero junior. Abre este archivo y reemplaza el perfil de ejemplo con tu propia información.

> [!WARNING]
> **Ética Profesional:** Sé completamente honesto con los datos que registras en tu perfil. El optimizador técnico está diseñado para pulir y elevar la redacción de tus logros reales para que resuenen más con los reclutadores, pero **bajo ninguna circunstancia inventará empleos o conocimientos que no posees**.

---

## 💻 Instrucciones de Uso y Nuevas Funcionalidades

El script principal ahora genera dos salidas automáticas simultáneas y te permite seleccionar el idioma final de tu currículum.

### Paso 1: Crear el archivo de la oferta laboral
Copia la descripción de la vacante, requisitos, tecnologías y responsabilidades directamente de LinkedIn u otra bolsa de trabajo, y pégala dentro de un archivo de texto plano en la raíz (por ejemplo, `job_description.txt`).

### Paso 2: Ejecutar el Optimizador
Ejecuta el script principal pasándole la ruta del archivo de la vacante:

```bash
python src/cv_optimizer.py --job job_description.txt
```

---

### 🌐 Optimización y Traducción Automática al Inglés (¡Nuevo Flag!)
Si estás aplicando a una posición internacional o en una compañía de tecnología global que requiere tu información en inglés, el script cuenta con un flag para traducir y optimizar de forma transparente:

```bash
python src/cv_optimizer.py --job job_description.txt --lang en
```

Parámetros del flag `-l` o `--lang`:
- `es` (por defecto): Genera todo el contenido y las cabeceras del CV en **Español**.
- `en`: Traduce de forma nativa e inteligente todo el contenido del CV y las cabeceras al **Inglés** aplicando el Efecto Pygmalion directamente en dicho idioma.

---

### 🎨 Personalización de la Plantilla HTML (¡Nuevo Flag! 🖌️)
Ahora puedes modificar completamente el diseño, los colores y la tipografía de tu currículum sin alterar el código Python. El sistema utiliza **Jinja2** para inyectar dinámicamente los datos optimizados por la IA en una plantilla HTML.

Para utilizar una plantilla específica:
```bash
python src/cv_optimizer.py --job job_description.txt --template templates/cv_template.html
```

Parámetros del flag `-t` o `--template`:
- `templates/cv_template.html` (por defecto): La plantilla premium prediseñada.
- Puedes copiar la plantilla por defecto, crear tu propio diseño en HTML/CSS, y pasar la ruta de tu plantilla personalizada.

#### ¿Cómo editar la plantilla predeterminada?
Abre el archivo [templates/cv_template.html](templates/cv_template.html) en tu editor de código. En la sección `<style>` puedes modificar:
- **Colores corporativos**: Ajustando las variables CSS como `--color-primary` (para texto principal), `--color-accent` (para líneas e íconos), etc.
- **Tipografía**: Cambiando la fuente cargada desde Google Fonts (por defecto, *Inter*).
- **Márgenes y Tamaños**: Modificando el tamaño de los márgenes o adaptando las reglas `@media print` para ajustar a una sola página.

---

### 📄 Salidas Automáticas: Markdown e HTML Premium (¡Nuevo!)
Cada vez que corres el optimizador, el script genera **dos archivos de salida** en tu carpeta `output/`:

1. **`output/optimized_cv.md` (Markdown):** Ideal para copiar rápidamente el texto a otros editores o realizar retoques de texto sencillos.
2. **`output/optimized_cv.html` (HTML Premium):** Un archivo interactivo que incluye una hoja de estilos CSS profesional integrada. Este archivo ha sido diseñado específicamente con reglas de maquetación de impresión (`@media print` y reglas `@page` de tamaño carta) y control de cortes de página (`page-break-inside: avoid`) en secciones clave.

#### ¿Cómo obtener un PDF impecable desde el HTML?
Para exportar tu currículum a un formato PDF profesional y listo para enviar a reclutadores:
1. Abre el archivo `output/optimized_cv.html` (o `output/optimized_cv.en.html` según corresponda) en cualquier navegador web moderno (Google Chrome, Safari, Firefox o Edge).
2. Abre el menú de impresión de tu navegador pulsando `Cmd + P` (en macOS) o `Ctrl + P` (en Windows/Linux).
3. En las opciones de destino, selecciona **"Guardar como PDF"** (Save as PDF).
4. Asegúrate de desactivar las casillas de *"Encabezados y pies de página"* del navegador y activar *"Gráficos de fondo"*.
5. Guarda el archivo. ¡Obtendrás un currículum PDF con una distribución de márgenes y tipografía impecable!

---

### 🤖 Entrevista Técnica Simulada (¡Nuevo Flag! 🎤)
El proyecto incluye un simulador de entrevista interactivo con IA que utiliza chat multi-turno (Chat Memory) y se restringe a evaluar **únicamente** tecnologías declaradas en el perfil original (CV) del candidato y requeridas en la descripción del puesto (JD). Tiene un límite estricto de 7 preguntas y al final genera un reporte de feedback y exporta la transcripción de la entrevista.

Para iniciar la entrevista técnica simulada:
```bash
python src/cv_optimizer.py --job job_description.txt --mock-interview
```

Al terminar, la transcripción se guardará automáticamente en:
- `output/interview_transcript.md`

---

### ⚖️ Auditor de Robustez / Robustness Judge (¡Nuevo Flag! 🔍)
Esta funcionalidad evalúa la calidad y veracidad del CV optimizado, comparándolo de forma minuciosa contra el perfil de origen (YAML) del candidato. A través de Structured Outputs (esquemas Pydantic), el modelo evalúa alucinaciones de la IA (datos fabricados o exagerados), inconsistencias de datos y compliance ético del currículum, entregando un veredicto general (Aprobado, Aprobado con observaciones, o Rechazado).

Para auditar un CV optimizado existente:
```bash
python src/cv_optimizer.py --job job_description.txt --robustness
```

El reporte de auditoría completo se guardará en formato estructurado JSON en:
- `output/robustness_report.json`

---

### 🎯 Plantilla Optimizada para ATS (¡Nuevo! 📝)
Los sistemas de seguimiento de candidatos (ATS) leen mejor currículums lineales, limpios y sencillos. Para maximizar tus probabilidades de pasar estos filtros automatizados, hemos creado una plantilla diseñada específicamente para este fin:
- **Sin emojis ni íconos:** Los caracteres especiales pueden corromper el análisis de texto en sistemas ATS antiguos.
- **Estructura lineal clara:** Sin tablas complejas ni columnas flotantes.
- **Tipografía estándar:** Utiliza Arial/Helvetica de alta compatibilidad.

Para generar tu CV optimizado con el formato ATS:
```bash
python src/cv_optimizer.py --job job_description.txt --template templates/cv_ats_template.html
```

---

## 🧪 Suite de Pruebas Unitarias

Para asegurar que todo el andamiaje funcione y para que aprendas sobre el Aseguramiento de Calidad (QA), el proyecto incluye pruebas unitarias automatizadas que simulan llamadas de API y verifican las salidas de texto.

Ejecuta las pruebas desde la raíz del proyecto corriendo:
```bash
PYTHONPATH=src python3 -m unittest src/test_cv_optimizer.py
```
