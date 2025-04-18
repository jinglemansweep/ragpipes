FROM python:3.12-slim

RUN pip install uv && \
    python -m venv /venv

COPY . /app/
WORKDIR /app/

RUN . /venv/bin/activate && uv sync --frozen

CMD ["uv", "run", "-m", "ragpipe"]
