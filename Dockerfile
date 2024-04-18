# build stage
FROM python:3.10.0 as builder

ARG PYPI_URL
ENV PYPI_URL=${PYPI_URL}

WORKDIR /app

RUN python -m venv /app/venv

ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir --extra-index-url $PYPI_URL -r requirements.txt


# app stage
FROM python:3.10.0

RUN groupadd -g 999 python && useradd -r -u 999 -g python python

RUN mkdir /app && chown python:python /app

WORKDIR /app

COPY --chown=python:python --from=builder /app/venv ./venv
COPY --chown=python:python src /app/src
#mkdir -p /app/data_pipe/data_temp && chown python:python /app/data_pipe/data_temp

USER 999

ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["python", "src/main.py"]
