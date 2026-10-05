FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.13
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "robotops.lab.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
