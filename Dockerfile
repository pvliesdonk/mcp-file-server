# Use official Python image as base
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Set working directory
WORKDIR /app

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

EXPOSE 3000

ENV TRANSPORT=streamable-gttp
ENV LOG_LEVEL=INFO
ENV HOST=0.0.0.0
ENV PORT=3000
ENV PATH=/data

CMD ["uv", "run", "mcp-file-server"]
VOLUME /data
