# Dockerfile for building the image for globallog.
FROM ghcr.io/astral-sh/uv:python3.11-alpine

# Authors
LABEL authors="Waterloo Rocketry <contact@waterloorocketry.com>"

# Install git.
# Required to build parsley dependency.
RUN apk add --no-cache git

# Copy the project into the image.
COPY . /app

# Sync the project into the new environment, asserting the lockfile is up to date.
WORKDIR /app
RUN uv sync --locked --no-editable --no-dev --package globallog

# Run the global logger.
ENTRYPOINT ["src/globallog/docker_entrypoint.sh"]
