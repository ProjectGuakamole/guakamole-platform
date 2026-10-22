FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system guakamole && adduser --system --ingroup guakamole guakamole

COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

COPY --chown=guakamole:guakamole app ./app
COPY --chown=guakamole:guakamole alembic ./alembic
COPY --chown=guakamole:guakamole scripts ./scripts
COPY --chown=guakamole:guakamole alembic.ini ./alembic.ini

USER guakamole

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
