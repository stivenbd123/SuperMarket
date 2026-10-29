FROM python:3.13-slim

# Chromium + su driver para Selenium, y curl para instalar Claude Code
RUN apt-get update \
    && apt-get install -y chromium chromium-driver curl \
    && rm -rf /var/lib/apt/lists/*

# Claude Code (el comando "claude")
RUN curl -fsSL https://claude.ai/install.sh | bash
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# El código no se copia: docker-compose.yml monta esta carpeta en /app,
# así lo que cambies en VS Code se usa en la siguiente corrida.
CMD ["python", "-u", "main.py"]
