# Web Personalizer - Personalización HTML con IA

Una aplicación web que permite personalizar páginas HTML usando inteligencia artificial (Google Gemini).

## Configuración

```bash
# 1. Copiar archivo de configuración
cp .env.example .env

# 2. Editar el archivo .env y configurar tu API key de Gemini
nano .env

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la aplicación
python app.py

```

## Obtener API Key de Gemini

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una nueva API key
3. Cópiala y pégala en el archivo `.env`

```bash
# En el archivo .env
GEMINI_API_KEY=tu_api_key_real_aqui
```

## Uso

1. Abre tu navegador en `http://localhost:8000`
2. Escribe una instrucción para personalizar la página
3. La IA modificará el HTML en tiempo real
4. Los cambios se guardan automáticamente por usuario

## Características

- Personalización HTML con IA
- Sesiones de usuario persistentes
- Protección de archivos sensibles
- Interfaz moderna y responsive
- Recarga automática tras cambios

## Desarrollo

### Estructura del proyecto
```
flask/
├── app.py              # Aplicación principal
├── requirements.txt    # Dependencias Python
├── .env.example       # Configuración de ejemplo
├── web_personalizer/  # Módulos de la aplicación
│   ├── index.html     # Página principal
│   ├── script.js      # Frontend JavaScript
│   ├── ai.py          # Integración con Gemini
│   └── usuarios/      # Archivos personalizados
└── README.md          # Este archivo
```

### Instalación de dependencias
```bash
pip install -r requirements.txt
```

### Variables de entorno disponibles
```bash
GEMINI_API_KEY=tu_api_key_aqui    # Requerida
FLASK_ENV=development             # Entorno
FLASK_DEBUG=true                  # Debug
PORT=8000                         # Puerto
HOST=0.0.0.0                      # Host
LOG_LEVEL=INFO                    # Nivel de log
```

## Seguridad

- El archivo `.env` está en `.gitignore` y no se sube a GitHub
- Cookies HTTP-only para sesiones
- Validación de entrada en todos los endpoints

## API Endpoints

- `GET /` - Página principal
- `POST /personalizar` - Personalizar HTML con IA
- `POST /reset` - Restablecer a la página original
- `GET /<archivo>` - Servir archivos estáticos (.html, .css, .js)
