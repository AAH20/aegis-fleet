FROM python:3.11-slim

LABEL maintainer="Ahmed Hassan <developer@a2zsoc.com>"
LABEL description="Aegis-Fleet: Autonomous Fleet Black-Box & GRC Assurance Plane"

WORKDIR /app

COPY pyproject.toml README.md ./
COPY aegis_fleet ./aegis_fleet
RUN pip install --no-cache-dir .

EXPOSE 8080

ENTRYPOINT ["aegis-fleet"]
CMD ["all"]
