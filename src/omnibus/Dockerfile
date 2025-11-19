# Dockerfile for building the image for omnibus-server.
FROM ghcr.io/astral-sh/uv:python3.11-alpine

# Authors
LABEL authors="Qian Qian <q23qian@uwaterloo.ca>"

# Expose the port the server will run on (5075, 5076, 5077).
EXPOSE 5075-5077

# Install git.
# Required to build parsley dependency.
RUN apk add --no-cache git

# Copy the project into the image.
COPY . /app

# Sync the project into the new environment, asserting the lockfile is up to date.
WORKDIR /app
RUN uv sync --locked

# Run the server.
ENTRYPOINT ["uv", "run", "omnibus-server"]
