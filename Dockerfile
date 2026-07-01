# Usamos una imagen base ligera de Python
FROM python:3.10-slim

# Instalamos dependencias del sistema necesarias para ffmpeg (para el audio)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Definimos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos y instalamos dependencias
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# El comando para arrancar la API usando el puerto que exige Cloud Run
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT

RUN pip install --upgrade pip
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
