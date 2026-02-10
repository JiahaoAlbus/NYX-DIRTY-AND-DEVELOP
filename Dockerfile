FROM python:3.11-slim

WORKDIR /app
COPY . /app

ENV PYTHONPATH="/app/apps/nyx-backend-gateway/src:/app/apps/nyx-backend/src"
ENV NYX_ENV="dev"

EXPOSE 8091

CMD ["python", "-m", "nyx_backend_gateway.server", "--host", "0.0.0.0", "--port", "8091", "--env-file", "/app/.env.example"]
