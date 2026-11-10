FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends gdal-bin libgdal-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir geopandas pyogrio shapely sqlalchemy "psycopg[binary]"
WORKDIR /workspace
