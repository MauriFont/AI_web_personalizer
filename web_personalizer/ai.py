"""
Módulo para procesamiento de HTML usando IA (Gemini)

Este módulo proporciona funciones para modificar archivos HTML utilizando
el modelo de IA Gemini (gemini-2.5-flash). Se encarga de la comunicación con la IA,
el procesamiento de las respuestas y la validación de resultados.

Características principales:
    - Integración con Gemini para procesamiento de lenguaje natural
    - Modificación de HTML/CSS (no JavaScript)
    - Validación robusta de respuestas de IA
    - Manejo de errores especializado
    - Logging detallado para debugging
    - Prompts optimizados para resultados consistentes

Excepciones personalizadas:
    - GeminiError: Errores de comunicación con Gemini
    - HTMLProcessingError: Errores de procesamiento de HTML
    - FileNotFoundError: Archivos no encontrados

Author: AI Assistant
Date: 2025-06-30
Version: 1.4.0
"""
import json
import logging
from google import genai
from pydantic import BaseModel
import enum
from google.genai import types

# Configurar logging con formato mejorado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def agregar_numeros_linea(html: str) -> str:
    """
    Agrega números de línea con formato más claro para evitar confusión
    
    Args:
        html (str): El HTML original sin números de línea
        
    Returns:
        str: HTML con números de línea con formato mejorado
        
    Example:
        >>> html = "<html>\\n<head>\\n</head>\\n</html>"
        >>> print(agregar_numeros_linea(html))
        [1] <html>
        [2] <head>
        [3] </head>
        [4] </html>
    """
    lineas = html.split('\n')
    lineas_numeradas = []
    
    for i, linea in enumerate(lineas, 1):
        # Usar formato más explícito que evite confusión
        numero_linea = f"[{i:3d}] "
        lineas_numeradas.append(numero_linea + linea)
    
    return '\n'.join(lineas_numeradas)

class GeminiError(Exception):
    """
    Excepción personalizada para errores relacionados con Gemini
    
    Se lanza cuando hay problemas de comunicación con el servidor Gemini,
    respuestas malformadas, o cuando el modelo no está disponible.
    
    Examples:
        >>> raise GeminiError("No se pudo conectar con Gemini API")
        >>> raise GeminiError("Modelo gemini-2.5-flash no encontrado")
    """
    pass


class HTMLProcessingError(Exception):
    """
    Excepción personalizada para errores de procesamiento de HTML
    
    Se lanza cuando hay problemas con el contenido HTML, parsing JSON,
    validación de estructura, o cuando la IA no puede procesar la solicitud.
    
    Examples:
        >>> raise HTMLProcessingError("Archivo HTML está vacío")
        >>> raise HTMLProcessingError("Respuesta de IA no válida")
    """
    pass


class FileNotFoundError(Exception):
    """
    Excepción personalizada para archivos no encontrados
    
    Se lanza cuando no se puede encontrar o leer el archivo index.html
    o cuando hay problemas de permisos de archivo.
    
    Examples:
        >>> raise FileNotFoundError("index.html no existe en el directorio")
        >>> raise FileNotFoundError("Sin permisos para leer index.html")
    """
    pass


def ejecutar_proceso_completo(modificacion: str, html_contenido: str) -> dict:
    """
    Ejecuta el proceso completo de modificación HTML usando cambios parciales
    
    Esta función es el punto de entrada principal para procesar solicitudes
    de modificación HTML. Ahora usa un enfoque de cambios parciales para 
    evitar problemas de truncamiento por límites de tokens.
    
    Args:
        modificacion (str): La modificación a aplicar al HTML
        html_contenido (str): El contenido HTML a modificar
    
    Returns:
        dict: Diccionario con la respuesta procesada y HTML modificado
        
    Raises:
        HTMLProcessingError: Si hay errores en el procesamiento
        GeminiError: Si hay errores en la comunicación con Gemini
        
    Example:
        >>> html = "<html><body><h1>Título</h1></body></html>"
        >>> resultado = ejecutar_proceso_completo("Cambia el color de fondo a azul", html)
        >>> if resultado["state"]:
        ...     print("HTML modificado exitosamente")
        ...     print(resultado["codigo"])  # HTML completo modificado
        ... else:
        ...     print(f"Error: {resultado['error']}")
    """
    try:
        logger.info(f"Iniciando procesamiento con cambios parciales...")
        
        # Validar que el contenido HTML no esté vacío
        if not html_contenido or not html_contenido.strip():
            raise HTMLProcessingError("El contenido HTML está vacío")
        
        logger.info("Procesando contenido HTML recibido...")
        html_original = html_contenido
        
        # Agregar números de línea para ayudar al modelo
        html_numerado = agregar_numeros_linea(html_original)

        # Obtener cambios parciales de Gemini
        respuesta_json = procesar_html_con_gemini(modificacion, html_numerado)
        
        # Parsear respuesta JSON
        try:
            resultado = json.loads(respuesta_json)
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear JSON de Gemini: {e}")
            raise HTMLProcessingError(f"Respuesta inválida de la IA: {str(e)}")
        
        # Validar estructura de respuesta
        if "state" not in resultado:
            logger.error("Respuesta de Gemini no tiene la estructura esperada")
            raise HTMLProcessingError("Respuesta de la IA no tiene el formato esperado")
        
        # Si hay error, devolver tal como está
        if resultado.get("state") == False:
            logger.info("La IA rechazó la solicitud")
            return resultado
        
        # Si hay cambios, aplicarlos al HTML original
        if "cambios" in resultado and resultado["cambios"]:
            try:
                # Aplicar cambios parciales
                html_modificado = aplicar_cambios_parciales(html_original, resultado["cambios"])
                
                # Devolver resultado con HTML completo modificado
                return {
                    "state": True,
                    "codigo": html_modificado,
                }
                
            except Exception as e:
                logger.error(f"Error aplicando cambios: {e}")
                raise HTMLProcessingError(f"No se pudieron aplicar los cambios: {str(e)}")
        else:
            logger.warning("No se recibieron cambios para aplicar")
            return {
                "state": False,
                "error": "La IA no proporcionó cambios específicos para aplicar"
            }
        
    except GeminiError as e:
        logger.error(f"Error de Gemini: {e}")
        return {
            "state": False,
            "error": f"Error de comunicación con la IA: {str(e)}"
        }
    except HTMLProcessingError as e:
        logger.error(f"Error de procesamiento HTML: {e}")
        return {
            "state": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return {
            "state": False,
            "error": f"Error interno del servidor: {str(e)}"
        }


def procesar_html_con_gemini(modificacion: str, html_numerado: str) -> str:
    """
    Procesa el archivo index.html con Gemini según la modificación especificada
    
    Esta función se encarga de la comunicación directa con Gemini, construyendo
    los prompts apropiados y gestionando la respuesta del modelo de IA.
    Ahora incluye números de línea para ayudar al modelo a ubicar elementos.
    
    Args:
        modificacion (str): La modificación a aplicar al HTML
        
    Returns:
        str: Respuesta JSON de Gemini con cambios parciales
        
    Raises:
        FileNotFoundError: Si el archivo index.html no existe
        GeminiError: Si hay errores en la comunicación con Gemini        Example:
        >>> respuesta = procesar_html_con_gemini("Añade un botón azul")
        >>> resultado = json.loads(respuesta)
    """
    try:
        # Validar parámetros de entrada
        if not modificacion or not modificacion.strip():
            raise HTMLProcessingError("La modificación no puede estar vacía")
        
        logger.info("Leyendo archivo HTML original...")
        
        logger.info("Construyendo prompt para Gemini con números de línea...")
        # Construir mensajes para Gemini con prompts mejorados para cambios parciales
        system = """Eres un experto en desarrollo web que analiza páginas HTML y proporciona cambios específicos.

INSTRUCCIONES CRÍTICAS SOBRE LÍNEAS:
1. El formato es: [123] contenido_de_la_linea
2. El número 123 ES el número de esa línea específica
3. Si quieres modificar el contenido que aparece después de [25], entonces 'linea' debe ser 25
4. NO te confundas: [25] marca EXACTAMENTE la línea número 25

INSTRUCCIONES DE CAMBIOS PARCIALES:
1. NO devuelvas el HTML completo
2. Devuelve SOLO los cambios necesarios basados en el HTML y CSS ACTUAL que acabas de leer
3. El campo 'a_reemplazar' DEBE contener texto que REALMENTE EXISTE en el HTML y CSS mostrado arriba
4. IGNORA LOS NÚMEROS DE LÍNEA en el campo 'a_reemplazar' - usa solo el contenido HTML real
6. Si no encuentras el texto exacto a modificar, busca texto similar o relacionado
7. Si la solicitud requiere JavaScript incluyendo inline como onclick, recházala con state: false
8. Sé muy preciso - el texto en 'a_reemplazar' debe coincidir EXACTAMENTE (sin números de línea)
9. Sí puedes usar CSS para cambiar estilos
10. Muy importante: No puedes modificar la etiqueta con clase 'input-bar' ni sus hijos.

TIPOS DE CAMBIO DISPONIBLES:
- "reemplazar": Reemplazar texto/elemento específico que EXISTE en el HTML y CSS
- "insertar": Insertar nuevo elemento en ubicación específica

Solo en el tipo reemplazar es obligatorio el campo 'a_reemplazar'.
Si el tipo es "insertar", entonces 'a_reemplazar' no es necesario y en el campo 'escribir' debes poner el nuevo contenido HTML.

EJEMPLO CORRECTO:
Si ves: [LINEA 15] <h1>Mi Título</h1>
Y quieres cambiar ese título, entonces:
- "linea": 15 (el número que aparece en [15])
- "a_reemplazar": "<h1>Mi Título</h1>" (SIN el marcador [15])

Devuelve la respuesta en este formato JSON exacto:

VALIDACIÓN FINAL:
Antes de responder, verifica:
1. ¿El número de 'linea' coincide exactamente con [XXX] donde está el contenido?
2. ¿El texto 'a_reemplazar' existe realmente después del marcador [XXX] correspondiente?
3. ¿Has omitido completamente los marcadores [XXX] en 'a_reemplazar' y 'escribir'?
4. ¿El HTML y CSS resultante es válido y no contiene JavaScript ni elementos inline como onclick?
"""

        mensaje = f"""

IMPORTANTE - LEE CUIDADOSAMENTE EL HTML ACTUAL CON NÚMEROS DE LÍNEA:
El HTML que vas a modificar es el siguiente. Cada línea tiene un número al inicio para ayudarte a ubicar elementos:

HTML ACTUAL (con números de línea): {html_numerado}

SOLICITUD DE MODIFICACIÓN: {modificacion}
"""
        

        class Tipo(enum.Enum):
            INSERTAR = "insertar"
            REEMPLAZAR = "reemplazar"

        class Cambio(BaseModel):
            tipo: Tipo
            linea: int
            a_reemplazar: str
            escribir: str

        class formato(BaseModel):
            state: bool
            cambios: list[Cambio] = []
            error: str = ""
        
        logger.info("Enviando solicitud a Gemini...")

        client = genai.Client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=mensaje,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                system_instruction=system,
                response_mime_type='application/json',
                response_schema=formato,
            )
        )
        
        print(response.text)
        # Validar respuesta de Gemini
        if not response.text:
            logger.error("Respuesta de Gemini está mal formada")
            raise GeminiError("Respuesta inválida de Gemini")
        
        seguro2, error2 = validar_javascript_prohibido(response.text)

        if not seguro2:
            logger.error(error2)
            raise HTMLProcessingError(error2)

        content = response.text

        # Log de debug para ver qué devuelve Gemini
        #logger.info(f"Respuesta de Gemini (primeros 500 chars): {content[:500]}...")
        
        if not content:
            logger.error("Gemini devolvió contenido vacío")
            raise GeminiError("Gemini devolvió una respuesta vacía")
        
        logger.info("Respuesta de Gemini recibida exitosamente")
        return content
        
    except (HTMLProcessingError, FileNotFoundError, GeminiError):
        # Re-lanzar excepciones conocidas
        raise
    except Exception as e:
        logger.error(f"Error inesperado en procesamiento: {e}")
        raise GeminiError(f"Error inesperado: {str(e)}")


def aplicar_cambios_parciales(html_original: str, cambios: list) -> str:
    """
    Aplica una lista de cambios parciales al HTML original
    
    Args:
        html_original (str): El HTML original sin modificar
        cambios (list): Lista de cambios a aplicar
        
    Returns:
        str: HTML con los cambios aplicados
        
    Raises:
        HTMLProcessingError: Si no se puede aplicar algún cambio
    """
    html_modificado = html_original
    cambios_aplicados = 0
    
    logger.info(f"Aplicando {len(cambios)} cambios al HTML...")
    
    for i, cambio in enumerate(cambios):
        try:
            # Validar campos requeridos
            campos_requeridos = ['tipo', 'linea', 'escribir']
            for campo in campos_requeridos:
                if campo not in cambio or not cambio[campo]:
                    raise HTMLProcessingError(f"Cambio {i+1} está incompleto: falta el campo '{campo}'")
            
            # Para tipo reemplazar, requerir campo 'a_reemplazar'
            if cambio['tipo'] == 'reemplazar':
                if 'a_reemplazar' not in cambio or not cambio['a_reemplazar']:
                    raise HTMLProcessingError(f"Cambio {i+1} está incompleto: falta el campo 'a_reemplazar'")
            
            tipo = cambio['tipo']
            linea = cambio['linea']
            a_reemplazar = cambio.get('a_reemplazar', '')
            escribir = cambio['escribir']
            
            logger.info(f"Aplicando cambio {i+1}")
            
            if tipo == 'reemplazar':
                if a_reemplazar:
                    html_temp, exitoso = reemplazar_html(html_modificado, linea, a_reemplazar, escribir)
                    if exitoso:
                        html_modificado = html_temp
                        cambios_aplicados += 1
                        logger.info(f"Reemplazo aplicado exitosamente")
                    else:
                        logger.warning(f"No se encontró el texto a reemplazar: {a_reemplazar[:50]}...")
                else:
                    logger.warning(f"Campo 'a_reemplazar' vacío para reemplazo")
                    
            elif tipo == 'insertar':
                html_temp, exitoso = insertar_html(html_modificado, linea, escribir)
                if exitoso:
                    html_modificado = html_temp
                    cambios_aplicados += 1
                    logger.info(f"Inserción aplicada exitosamente")
                else:
                    logger.warning(f"No se pudo insertar en la línea especificada: {linea}")
                    
            else:
                logger.warning(f"Tipo de cambio desconocido: {tipo}")
                
        except Exception as e:
            logger.error(f"Error aplicando cambio {i+1}: {e}")
            descripcion_fallback = cambio.get('descripcion', f'Cambio {i+1}')
            raise HTMLProcessingError(f"No se pudo aplicar el cambio: {descripcion_fallback}. Error: {str(e)}")
    
    logger.info(f"Se aplicaron {cambios_aplicados} de {len(cambios)} cambios")
    
    if cambios_aplicados == 0:
        raise HTMLProcessingError("No se pudo aplicar ningún cambio. Verifica que el HTML original coincida con los patrones de búsqueda.")
    
    # Reemplazar todos los [n] por saltos de línea reales
    html_modificado = html_modificado.replace("[n]", "\n")

    return html_modificado


def reemplazar_html(html_modificado: str, linea: int, reemplazar: str, escribir: str) -> tuple:
    """
    Busca en html_modificado la línea indicada por 'linea', encuentra el texto 'reemplazar'
    y lo reemplaza por 'escribir'. Devuelve (nuevo_html, True) si tuvo éxito, o (html_modificado, False) si no.
    """
    lineas = html_modificado.split('\n')
    idx = linea - 1  # Las líneas están numeradas desde 1
    if 0 <= idx < len(lineas):
        if reemplazar in lineas[idx]:
            lineas[idx] = lineas[idx].replace(reemplazar, escribir, 1)
            return ('\n'.join(lineas), True)
    return (html_modificado, False)

def insertar_html(html_modificado: str, linea: int, escribir: str) -> tuple:
    """
    Inserta el texto 'escribir' al inicio de la línea indicada por 'linea' en html_modificado.
    Devuelve (nuevo_html, True) si tuvo éxito, o (html_modificado, False) si la línea no existe.
    """
    lineas = html_modificado.split('\n')
    idx = linea - 1  # Las líneas están numeradas desde 1
    if 0 <= idx < len(lineas):
        lineas[idx] = escribir + "[n]" + lineas[idx]
        return ('\n'.join(lineas), True)
    return (html_modificado, False)

def validar_javascript_prohibido(contenido: str) -> tuple:
    """
    Valida que el contenido no contenga JavaScript de ningún tipo
    
    Args:
        contenido (str): El contenido a validar
        
    Returns:
        tuple: (es_seguro: bool, mensaje_error: str)
    """
    contenido_lower = contenido.lower()
    
    # Detectar elementos script
    if '<script' in contenido_lower or 'javascript:' in contenido_lower:
        return False, "Detectado uso de <script> o javascript: - no permitido"
    
    # Detectar eventos inline (la lista más completa)
    eventos_js = [
        'onclick', 'ondblclick', 'onmousedown', 'onmouseup', 'onmouseover', 
        'onmouseout', 'onmousemove', 'onkeydown', 'onkeyup', 'onkeypress',
        'onload', 'onunload', 'onresize', 'onscroll', 'onfocus', 'onblur',
        'onchange', 'onsubmit', 'onreset', 'onselect', 'onabort', 'onerror',
        'oncontextmenu', 'ondrag', 'ondragend', 'ondragenter', 'ondragleave',
        'ondragover', 'ondragstart', 'ondrop', 'oninput', 'oninvalid',
        'ontouchstart', 'ontouchmove', 'ontouchend', 'ontouchcancel',
        'onwheel', 'onanimationstart', 'onanimationend', 'onanimationiteration',
        'ontransitionend', 'oncanplay', 'oncanplaythrough', 'ondurationchange',
        'onemptied', 'onended', 'onloadeddata', 'onloadedmetadata',
        'onloadstart', 'onpause', 'onplay', 'onplaying', 'onprogress',
        'onratechange', 'onseeked', 'onseeking', 'onstalled', 'onsuspend',
        'ontimeupdate', 'onvolumechange', 'onwaiting'
    ]
    
    for evento in eventos_js:
        if evento in contenido_lower:
            return False, f"Detectado evento JavaScript '{evento}' - no permitido por seguridad"
    
    # Detectar eval, Function y otras funciones peligrosas
    funciones_peligrosas = [
        'eval(', 'function(', 'new function', 'settimeout', 'setinterval',
        'document.write', 'innerhtml', 'outerhtml', 'insertadjacenthtml'
    ]
    
    for funcion in funciones_peligrosas:
        if funcion in contenido_lower:
            return False, f"Detectada función peligrosa '{funcion}' - no permitida"
    
    return True, "Contenido seguro"