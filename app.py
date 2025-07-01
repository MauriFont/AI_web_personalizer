#!/usr/bin/env python3
"""
Aplicación Flask para servir archivos estáticos
"""
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import os
import sys
import logging
import uuid
from pathlib import Path
from web_personalizer.ai import ejecutar_proceso_completo, HTMLProcessingError, GeminiError

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

# Configurar Flask desde variables de entorno
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB por defecto

# Configuración de cookies desde variables de entorno
COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
COOKIE_MAX_AGE = int(os.getenv('COOKIE_MAX_AGE', '2592000'))  # 30 días por defecto

# Habilitar CORS para todas las rutas
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

# Directorio actual donde están los archivos estáticos
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

def obtener_o_crear_usuario_id(user_id=None):
    """
    Obtiene o crea un ID de usuario único para gestión de sesiones
    """
    if user_id is None or not user_id.strip():
        nuevo_id = str(uuid.uuid4())
        print(f"Generando nuevo ID de usuario: {nuevo_id[:8]}...")
        return nuevo_id
    
    print(f"Usando ID de usuario existente: {user_id[:8]}...")
    return user_id

def crear_carpeta_usuario(user_id):
    """
    Crea la carpeta personalizada para el usuario si no existe
    """
    try:
        carpeta_usuario = f"web_personalizer/usuarios/{user_id}"
        Path(carpeta_usuario).mkdir(parents=True, exist_ok=True)
        print(f"Carpeta de usuario preparada: {carpeta_usuario}")
        return carpeta_usuario
    except OSError as e:
        print(f"Error al crear carpeta de usuario: {e}")
        raise

def guardar_html_procesado(contenido_html, user_id, nombre_archivo='index.html'):
    """
    Guarda el contenido HTML procesado en la carpeta del usuario
    """
    try:
        # Crear carpeta del usuario si no existe
        carpeta_usuario = crear_carpeta_usuario(user_id)
        ruta_completa = os.path.join(carpeta_usuario, nombre_archivo)
        
        # Validar contenido antes de guardar
        if not contenido_html or not contenido_html.strip():
            raise ValueError("El contenido HTML está vacío")
        
        # Escribir archivo con encoding UTF-8 para soporte de caracteres especiales
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            f.write(contenido_html)
        
        print(f"Archivo guardado exitosamente: {ruta_completa}")
        return ruta_completa
        
    except (IOError, OSError) as e:
        print(f"Error al guardar archivo HTML: {e}")
        raise
    except ValueError as e:
        print(f"Error de validación: {e}")
        raise

@app.route('/')
def index():
    """Servir index.html personalizado del usuario o el general"""
    try:
        # Obtener user_id de cookies
        user_id = request.cookies.get("user_id")
        
        # Si tiene user_id, buscar su archivo personalizado
        if user_id:
            ruta_personalizada = f"web_personalizer/usuarios/{user_id}/index.html"
            if os.path.exists(ruta_personalizada):
                print(f"Sirviendo archivo personalizado: {ruta_personalizada}")
                return send_file(ruta_personalizada)
        
        # Si no tiene user_id o no existe archivo personalizado, servir el general
        print("Sirviendo archivo index.html general")
        return send_file(os.path.join(STATIC_DIR, 'web_personalizer/index.html'))
    except FileNotFoundError:
        return "Error: Archivo index.html no encontrado", 404

@app.route('/<path:filename>')
def static_files(filename):
    """Servir solo archivos HTML y CSS por seguridad"""
    # Extensiones permitidas
    extensiones_permitidas = {'.html', '.css', '.js'}
    
    # Obtener la extensión del archivo
    _, extension = os.path.splitext(filename.lower())
    
    # Verificar que la extensión esté permitida
    if extension not in extensiones_permitidas:
        logger.warning(f"Intento de acceso a archivo no permitido: {filename}")
        return jsonify({
            "state": False,
            "error": f"Tipo de archivo no permitido. Solo se permiten archivos HTML y CSS."
        }), 403
    
    try:
        return send_from_directory(STATIC_DIR+"/web_personalizer/", filename)
    except FileNotFoundError:
        return f"Error: Archivo {filename} no encontrado", 404

@app.route('/personalizar', methods=['POST'])
def personalizar_html():
    """
    Endpoint principal para personalizar HTML usando IA
    """
    try:
        # Verificar que la petición tenga JSON
        if not request.is_json:
            return jsonify({
                "state": False,
                "error": "El contenido debe ser JSON"
            }), 400
        
        data = request.get_json()
        
        # Verificar que exista el campo 'message' (manteniendo compatibilidad con restapi.py)
        if not data or 'message' not in data:
            return jsonify({
                "state": False,
                "error": "Campo 'message' requerido"
            }), 400
        
        message = data['message']
        
        if not message or not message.strip():
            return jsonify({
                "state": False,
                "error": "El mensaje no puede estar vacío"
            }), 400
        
        # Obtener user_id de cookies o generar uno nuevo
        user_id = request.cookies.get("user_id")
        user_id = obtener_o_crear_usuario_id(user_id)
        
        logger.info(f"Procesando solicitud: {message[:50]}...")
        
        # Determinar qué archivo HTML leer (personalizado o genérico)
        archivo_html = 'web_personalizer/index.html'  # Archivo genérico por defecto
        
        if user_id:
            archivo_personalizado = f'web_personalizer/usuarios/{user_id}/index.html'
            if os.path.exists(archivo_personalizado):
                archivo_html = archivo_personalizado
                logger.info(f"Usando archivo personalizado: {archivo_html}")
            else:
                logger.info(f"No existe archivo personalizado para usuario {user_id[:8]}..., usando genérico")
        else:
            logger.info("No se proporcionó user_id, usando archivo genérico")
        
        # Leer el contenido HTML a modificar
        try:
            with open(archivo_html, 'r', encoding='utf-8') as f:
                html_contenido = f.read()
            logger.info(f"Archivo HTML leído exitosamente: {archivo_html}")
        except FileNotFoundError:
            logger.error(f"Archivo {archivo_html} no encontrado")
            return jsonify({
                "state": False,
                "error": f"El archivo {archivo_html} no existe"
            }), 404
        except IOError as e:
            logger.error(f"Error al leer {archivo_html}: {e}")
            return jsonify({
                "state": False,
                "error": f"No se pudo leer el archivo HTML: {str(e)}"
            }), 500
        
        # Procesar con IA pasando el contenido HTML
        resultado = ejecutar_proceso_completo(message, html_contenido)
        
        # Si fue exitoso, guardar el HTML en la carpeta del usuario
        if resultado.get("state") == True and "codigo" in resultado:
            try:
                guardar_html_procesado(resultado.get("codigo"), user_id, "index.html")
                
                # Crear respuesta HTML directa para recargar la página
                response = jsonify({"state": True})
                response.set_cookie(
                    key="user_id", 
                    value=user_id, 
                    max_age=COOKIE_MAX_AGE,
                    httponly=True,
                    secure=COOKIE_SECURE
                )
                
                return response
                
            except Exception as e:
                # Si falla el guardado, devolver error
                print(f"Error: No se pudo guardar el archivo HTML: {e}")
                return jsonify({
                    "state": False,
                    "error": f"Error guardando archivo: {str(e)}"
                }), 500
        else:
            # Si el resultado no es exitoso, devolver el JSON con error
            response = jsonify(resultado)
            response.set_cookie(
                key="user_id", 
                value=user_id, 
                max_age=COOKIE_MAX_AGE,
                httponly=True,
                secure=COOKIE_SECURE
            )
            return response
        
    except GeminiError as e:
        logger.error(f"Error de Gemini: {e}")
        return jsonify({
            "state": False,
            "error": f"Error de comunicación con la IA: {str(e)}"
        }), 502
        
    except HTMLProcessingError as e:
        logger.error(f"Error de procesamiento: {e}")
        return jsonify({
            "state": False,
            "error": f"Error de procesamiento: {str(e)}"
        }), 400
        
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({
            "state": False,
            "error": "Error interno del servidor. Por favor, intentalo de nuevo."
        }), 500

@app.route('/reset', methods=['POST'])
def reset_usuario():
    """
    Endpoint para restablecer el usuario a la página original
    eliminando su archivo personalizado
    """
    try:
        # Obtener user_id de cookies
        user_id = request.cookies.get("user_id")
        
        if not user_id:
            return jsonify({
                "state": False,
                "error": "No hay usuario identificado para restablecer"
            }), 400
        
        # Ruta del archivo personalizado del usuario
        ruta_personalizada = f"web_personalizer/usuarios/{user_id}/index.html"
        
        # Verificar si existe el archivo personalizado
        if os.path.exists(ruta_personalizada):
            try:
                # Eliminar el archivo personalizado
                os.remove(ruta_personalizada)
                logger.info(f"Archivo personalizado eliminado: {ruta_personalizada}")
                
                return jsonify({
                    "state": True,
                    "message": "Página restablecida a la versión original"
                }), 200
                
            except OSError as e:
                logger.error(f"Error al eliminar archivo personalizado: {e}")
                return jsonify({
                    "state": False,
                    "error": f"Error al eliminar el archivo personalizado: {str(e)}"
                }), 500
        else:
            # No hay archivo personalizado, ya está en la versión original
            return jsonify({
                "state": True,
                "message": "Ya estás viendo la página original"
            }), 200
            
    except Exception as e:
        logger.error(f"Error inesperado en reset: {e}")
        return jsonify({
            "state": False,
            "error": "Error interno del servidor"
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Manejador de errores 404"""
    return jsonify({
        "state": False,
        "error": "Recurso no encontrado"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejador de errores 500"""
    return jsonify({
        "state": False,
        "error": "Error interno del servidor"
    }), 500

if __name__ == "__main__":
    # Obtener configuración del servidor desde variables de entorno
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '8000'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    print("=" * 60)
    print("INICIANDO SERVIDOR WEB")
    print("=" * 60)
    print("Directorio actual:", os.getcwd())
    print(f"Entorno: {FLASK_ENV}")
    print(f"Debug: {FLASK_DEBUG}")
    print()
    print(f"Servidor WEB: http://{HOST}:{PORT}")
    print(f"   Pagina principal: http://{HOST}:{PORT}/")
    print(f"   Archivos estaticos: http://{HOST}:{PORT}/<archivo>")
    print(f"   API Personalizar: http://{HOST}:{PORT}/personalizar")
    print()
    
    # Verificar API key de Gemini
    gemini_key = os.getenv('GEMINI_API_KEY')
    if not gemini_key or gemini_key == 'tu_api_key_de_gemini_aqui':
        print("⚠️  ADVERTENCIA: API key de Gemini no configurada!")
        print("   Configúrala en el archivo .env: GEMINI_API_KEY=tu_clave_aqui")
        print("   Obtén tu clave en: https://makersuite.google.com/app/apikey")
        print()
    else:
        print(f"✅ API key de Gemini configurada: {gemini_key[:10]}...")
        print()
    
    print("Para detener el servidor presiona Ctrl+C")
    print("=" * 60)
    
    try:
        # Ejecutar la aplicación Flask
        app.run(
            host=HOST,
            port=PORT,
            debug=FLASK_DEBUG,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario")
    except ImportError as e:
        print(f"Error importando la aplicacion Flask: {e}")
        print("Asegurate de que app.py existe y es valido")
        sys.exit(1)
    except Exception as e:
        print(f"Error al iniciar servidor: {e}")
        sys.exit(1)