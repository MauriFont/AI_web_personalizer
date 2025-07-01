/**
 * Frontend JavaScript para HTML Personalizer
 * 
 * Este archivo maneja toda la lógica del frontend para comunicarse con el servidor,
 * gestionar cookies de usuario, mostrar respuestas y manejar errores.
 * 
 * Funcionalidades principales:
 * - Gestión de cookies para identificación de usuario
 * - Envío de solicitudes de modificación HTML
 * - Manejo de respuestas y errores
 * - Interface de usuario para logs y resultados
 * 
 * @author Mauricio Fontebasso
 * @version 1.3.0
 * @date 2025-06-28
 */

// Configuración del servidor
const SERVER_BASE_URL = window.location.origin;

/**
 * Alterna la visibilidad del área de respuestas
 */
function toggleResponseArea() {
    const responseArea = document.getElementById('responseArea');
    responseArea.classList.toggle('open');
}

/**
 * Muestra el área de respuestas (la abre si está cerrada)
 */
function showResponseArea() {
    const responseArea = document.getElementById('responseArea');
    responseArea.classList.add('open');
}

/**
 * Añade una respuesta al contenedor de respuestas con formato y timestamp
 * 
 * @param {string} type - Tipo de respuesta ('success' o 'error')
 * @param {string} content - Contenido del mensaje a mostrar
 * @param {string|null} timestamp - Timestamp personalizado (opcional)
 */
function addResponseToContainer(type, content, timestamp = null) {
    const container = document.getElementById('responseContainer');
    const noResponsesMsg = container.querySelector('.no-responses');
    
    // Remover el mensaje "no hay respuestas" si existe
    if (noResponsesMsg) {
        noResponsesMsg.remove();
    }
    
    // Mostrar el área de respuestas automáticamente
    showResponseArea();
    
    // Crear elemento de respuesta con estilos apropiados
    const responseItem = document.createElement('div');
    responseItem.className = 'response-item';
    
    const time = timestamp || new Date().toLocaleString('es-ES');
    
    responseItem.innerHTML = `
        <div class="response-header">
            <span class="response-type ${type}">${type === 'success' ? 'Exitoso' : 'Error'}</span>
            <span class="response-timestamp">${time}</span>
        </div>
        <div class="response-content">${content}</div>
    `;
    
    // Agregar al principio del contenedor (más reciente arriba)
    container.insertBefore(responseItem, container.firstChild);
    
    // Scroll suave hacia la respuesta más reciente
    responseItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Envía un mensaje a la servidor para procesar modificaciones HTML
 * 
 * Esta función maneja todo el flujo de comunicación con el servidor:
 * 1. Validación de entrada
 * 2. Preparación de la solicitud
 * 3. Envío al sevidor
 * 4. Procesamiento de respuesta
 * 5. Manejo de errores
 * 
 * @async
 * @function sendMessage
 * @returns {Promise<void>}
 */
async function sendMessage() {
    const input = document.getElementById('textInput');
    const button = document.getElementById('sendButton');
    const message = input.value.trim();
    
    // Validación de entrada
    if (!message) {
        addResponseToContainer('error', 'Por favor, escribe un mensaje antes de enviar');
        return;
    }
    
    // Deshabilitar el botón mientras se procesa la solicitud
    button.disabled = true;
    button.textContent = 'Enviando...';
    
    try {
        // Preparar solicitud al servidor
        const url = `${SERVER_BASE_URL}/personalizar`;
        console.log('Enviando mensaje a:', url);
        console.log('Mensaje:', message);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Incluir cookies automáticamente para gestión de usuario
            mode: 'cors',  // Asegurar que use CORS
            body: JSON.stringify({
                message: message,
                timestamp: new Date().toISOString()
            })
        });
        
        console.log('Respuesta del servidor:', response.status, response.statusText);
        console.log('Content-Type de respuesta:', response.headers.get('content-type'));
        
        if (response.ok) {
            const result = await response.json();

            console.log('Estructura de respuesta JSON:', result);
            
            if (result.state === true) {
                
                // Recargar la página para mostrar la nueva versión
                window.location.reload();
                
            } else if (result.state === false && result.error) {
                // Manejar errores de procesamiento
                 addResponseToContainer('error', 
                    `No se pudo procesar la solicitud:\n${result.error}\n`
                );

            } else {
                // Tipo de contenido no reconocido
                console.warn('Tipo de contenido no reconocido:', contentType);
                addResponseToContainer('error', 
                    `Respuesta del servidor en formato no reconocido. Por favor, intenta nuevamente.`
                );
            }
            
            input.value = ''; // Limpiar el campo
        } else {
            // Manejo mejorado de errores
            let errorMessage = `Error del servidor: ${response.status} - ${response.statusText}`;
            
            if (response.status === 501) {
                errorMessage += '\n\nEl servicio no está disponible en este momento. Por favor, intenta más tarde.';
            } else if (response.status === 404) {
                errorMessage += '\n\nServicio no encontrado. Por favor, intenta más tarde.';
            } else if (response.status === 500) {
                try {
                    const errorData = await response.json();
                    errorMessage += `\n\nError interno del servidor.`;
                } catch (e) {
                    errorMessage += '\n\nError interno del servidor.';
                }
            }
            
            throw new Error(errorMessage);
        }
    } catch (error) {
        console.error('Error al enviar mensaje:', error);
        addResponseToContainer('error', `Error al enviar mensaje: ${error.message}`);
    } finally {
        // Rehabilitar el botón
        button.disabled = false;
        button.textContent = 'Enviar';
    }
}

/**
 * Restablece la página a su estado original eliminando el archivo personalizado del usuario
 * 
 * @async
 * @function resetToOriginal
 * @returns {Promise<void>}
 */
async function resetToOriginal() {
    const resetButton = document.getElementById('resetButton');
    
    // Confirmar la acción con el usuario
    if (!confirm('¿Estás seguro de que quieres volver a la página original? Se perderán todas las modificaciones personalizadas.')) {
        return;
    }
    
    // Deshabilitar el botón mientras se procesa
    resetButton.disabled = true;
    resetButton.textContent = 'Restableciendo...';
    
    try {
        const url = `${SERVER_BASE_URL}/reset`;
        console.log('Enviando petición de reset a:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Incluir cookies para identificar al usuario
            mode: 'cors'
        });
        
        console.log('Respuesta de reset:', response.status, response.statusText);
        
        if (response.ok) {
            // Recargar la página para mostrar la version original
            console.log('Reset exitoso, recargando página...');
            window.location.reload();
        } else {
            let errorMessage = `Error al restablecer: ${response.status} - ${response.statusText}`;
            
            // Intentar obtener más detalles del error
            try {
                const errorData = await response.json();
                if (errorData.error) {
                    errorMessage = errorData.error;
                }
            } catch (e) {
                // Si no se puede parsear como JSON, usar el mensaje genérico
            }
            
            addResponseToContainer('error', `Error al restablecer la página: ${errorMessage}`);
        }
    } catch (error) {
        console.error('Error al restablecer:', error);
        addResponseToContainer('error', `Error de conexión al restablecer: ${error.message}`);
    } finally {
        // Rehabilitar el botón
        resetButton.disabled = false;
        resetButton.textContent = 'Volver a original';
    }
}

// Configurar event listeners cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    /**
     * Configurar el evento Enter en el campo de texto para envío rápido
     */
    document.getElementById('textInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    /**
     * Configurar el botón de envío
     */
    document.getElementById('sendButton').addEventListener('click', function() {
        sendMessage();
    });
    
    /**
     * Configurar el botón de reset
     */
    document.getElementById('resetButton').addEventListener('click', function() {
        resetToOriginal();
    });
    
    /**
     * Configurar el botón de cerrar área de respuestas
     */
    document.getElementById('closeResponseArea').addEventListener('click', function() {
        toggleResponseArea();
    });
    
    console.log('Event listeners configurados correctamente');
});
