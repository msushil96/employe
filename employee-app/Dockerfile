FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY app.py .
COPY templates/ templates/

ENV APP_PORT=5000
EXPOSE 5000

# Container-level health check (Docker native, independent of any orchestrator)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,os,sys; \
  urllib.request.urlopen(f'http://localhost:{os.getenv(\"APP_PORT\",\"5000\")}/health').getcode()==200 or sys.exit(1)" || exit 1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
