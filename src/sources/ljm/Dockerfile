# Dockerfile for building the image for omnibus-source-ljm.

# Stage 1: Download and extract the LJM installer
FROM alpine:3.21 AS downloader

RUN apk add --no-cache wget unzip

WORKDIR /ljm
RUN if [ "$(uname -m)" = "x86_64" ]; then \
    echo "Downloading LJM for Linux x64..."; \
    wget --progress=bar:force:noscroll -O ljm.zip https://files.labjack.com/installers/LJM/Linux/x64/release/LabJack-LJM_2025-05-07.zip; \
    echo "Checking sha256sum..."; \
    echo "d6a809d61b7beee786a97e1def7061bd1f31448232db32498502feb4e8726bce ljm.zip" | sha256sum -c; \
    unzip ljm.zip && rm ljm.zip; \
    elif [ "$(uname -m)" = "aarch64" ]; then \
    echo "Downloading LJM for Linux aarch64..."; \
    wget --progress=bar:force:noscroll -O ljm.zip https://files.labjack.com/installers/LJM/Linux/AArch64/release/LabJack-LJM_2025-05-07.zip; \
    echo "Checking sha256sum..."; \
    echo "47b7804b7636e367d3d6ce5cde84057549826880d0d8d496fd610c1c6765c798 ljm.zip" | sha256sum -c; \
    unzip ljm.zip && rm ljm.zip; \
    else \
    echo "Unsupported architecture: $(uname -m)" >&2; \
    exit 1; \
    fi

# Stage 2: Build the runtime image
FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim

# Authors
LABEL authors="Waterloo Rocketry <contact@waterloorocketry.com>"

# Install runtime dependencies with apt cache mount
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    bash \
    libusb-1.0-0-dev \
    git

# Install LJM from the downloader stage
RUN --mount=type=bind,from=downloader,source=/ljm,target=/ljm \
    /ljm/labjack_ljm_installer.run -- --without-kipling --no-restart-device-rules || [ $? -eq 2 ]

## OMNIBUS SETUP
# Copy the project into the image.
COPY . /app

# Sync the project into the new environment, asserting the lockfile is up to date.
WORKDIR /app
RUN uv sync --locked --no-editable --no-dev --package ljm-source

# Run the source.
ENTRYPOINT ["src/sources/ljm/docker_entrypoint.sh"]
