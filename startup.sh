#!/bin/bash

echo "Iniciando chatbot Flask en Azure..."

# Instalar dependencias si no están (opcional pero útil)
pip install --upgrade pip
pip install -r requirements.txt

# Ejecutar con gunicorn (Flask se llama 'app' en tu script principal)
gunicorn --bind=0.0.0.0:${PORT:-5000} app:app
