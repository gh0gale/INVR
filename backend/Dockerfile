# INVR backend. See deployment_plan.md §2.3.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# requirements.txt is fully == pinned by `uv export`, and CI fails if it drifts
# from uv.lock. Copied first so this layer caches independently of source.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run as an unprivileged user. The local file cache is the only thing written.
RUN useradd --create-home --uid 1000 invr && mkdir -p /app/.local_cache && chown -R invr /app
USER invr

EXPOSE 8000

# The platform supplies $PORT. Workers stay low deliberately: each analysis
# holds one for several seconds (audit MU-05), and a free instance has little
# memory to spread across processes.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --proxy-headers --forwarded-allow-ips='*'"]
