# --- Stage 1: build the Vue 3 frontend ---
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# vite.config.js outputs straight into ../backend/static
RUN npm run build

# --- Stage 2: Python backend, serving the built frontend as static files ---
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /app/backend/static ./static

# Train the models at image build time so container startup is instant
# and no retraining ever happens per-request.
RUN python train_models.py

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
