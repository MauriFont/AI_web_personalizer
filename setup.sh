#!/bin/bash

# Script de configuración rápida para Web Personalizer
# Ejecutar con: bash setup.sh

echo "========================================"
echo "   CONFIGURACIÓN WEB PERSONALIZER"
echo "========================================"
echo

# Verificar si ya existe .env
if [ -f ".env" ]; then
    echo "⚠️  El archivo .env ya existe."
    read -p "¿Quieres sobrescribirlo? (y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "❌ Configuración cancelada."
        exit 1
    fi
fi

# Copiar el archivo de ejemplo
cp .env.example .env
echo "✅ Archivo .env creado desde .env.example"

# Solicitar la API key de Gemini
echo
echo "🔑 CONFIGURACIÓN DE API KEY DE GEMINI"
echo "------------------------------------"
echo "1. Ve a: https://makersuite.google.com/app/apikey"
echo "2. Crea una nueva API key"
echo "3. Cópiala y pégala aquí"
echo

read -p "Ingresa tu API key de Gemini: " api_key

if [ -z "$api_key" ]; then
    echo "❌ Error: No se proporcionó una API key"
    echo "   Puedes editarla manualmente en el archivo .env"
else
    # Reemplazar la API key en el archivo .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/tu_api_key_de_gemini_aqui/$api_key/" .env
    else
        # Linux
        sed -i "s/tu_api_key_de_gemini_aqui/$api_key/" .env
    fi
    echo "✅ API key configurada correctamente"
fi

echo
echo "🚀 CONFIGURACIÓN COMPLETADA"
echo "============================"
echo "Próximos pasos:"
echo "1. Instala las dependencias: pip install -r requirements.txt"
echo "2. Ejecuta la aplicación: python app.py"
echo "3. Abre tu navegador en: http://localhost:8000"
echo
echo "📁 Archivos importantes:"
echo "   - .env (tu configuración privada)"
echo "   - app.py (aplicación principal)"
echo "   - requirements.txt (dependencias)"
echo
echo "💡 Tip: El archivo .env no se sube a GitHub por seguridad"
echo "========================================"
