FROM ghcr.io/astral-sh/uv:python3.11-alpine

# Authors
LABEL authors="Waterloo Rocketry <contact@waterloorocketry.com>"

# Install git.
RUN apk add --no-cache git

# Copy the project into the image.
WORKDIR /app
COPY . /app

# Sync the project into the new environment, asserting the lockfile is up to date.
RUN uv sync --no-dev --no-editable --locked --package parsley-source

# Set default Omnibus server
ENV OMNIBUS_SERVER_HOST="localhost"

# Run the server.
ENTRYPOINT ["uv","run", "--no-sync", "src/sources/parsley/main.py"]
CMD ["--quiet", "/dev/ttyUSB0"]
