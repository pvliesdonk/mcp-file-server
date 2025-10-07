# Use official Python image as base
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set working directory
WORKDIR /app

EXPOSE 3000

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

CMD ["mcp-file-server"]
VOLUME /data

USER 1000:1000

# Copy the project into the image
ADD . /app


ENV TRANSPORT=streamable-http
ENV LOG_LEVEL=INFO
ENV HOST=0.0.0.0
ENV PORT=3000
ENV PATH=/data

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Sync the project into a new environment, asserting the lockfile is up to date
RUN uv sync --locked --no-dev

