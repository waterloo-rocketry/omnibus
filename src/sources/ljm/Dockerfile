# Dockerfile for building the image for omnibus-source-ljm.
FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim

# Authors
LABEL authors="Waterloo Rocketry <contact@waterloorocketry.com>"

RUN echo "Building Omnibus LJM Source for $(uname -a)"

# Install dependencies.
RUN apt-get update && apt-get install wget bash git unzip libusb-1.0-0-dev -y

# Download correct LJM source for platform
WORKDIR /ljm
RUN if [ "$(uname -m)" = "x86_64" ]; then \
    echo "Bundling LJM for Linux x64..."; \
    wget --progress=bar:force:noscroll -O ljm.zip https://files.labjack.com/installers/LJM/Linux/x64/release/LabJack-LJM_2025-05-07.zip; \
    echo "Checking sha256sum..."; \
    echo "d6a809d61b7beee786a97e1def7061bd1f31448232db32498502feb4e8726bce ljm.zip" | sha256sum --check; \
    elif [ "$(uname -m)" = "aarch64" ]; then \
    echo "Building LJM for Linux aarch64..."; \
    wget --progress=bar:force:noscroll -O ljm.zip https://files.labjack.com/installers/LJM/Linux/AArch64/release/LabJack-LJM_2025-05-07.zip; \
    echo "Checking sha256sum..."; \
    echo "47b7804b7636e367d3d6ce5cde84057549826880d0d8d496fd610c1c6765c798 ljm.zip" | sha256sum --check; \
    else \
    echo "Unsupported architecture: $(uname -m)" >&2; \
    exit 1; \
    fi

# Install LabJack LJM
RUN unzip ljm.zip
RUN ./labjack_ljm_installer.run -- --without-kipling --no-restart-device-rules || [ $? -eq 2 ] # There's no udev folder in the container so script will always exit with $? == 2

# Cleanup LJM Install Files

WORKDIR /
RUN rm -r /ljm

## OMNIBUS SETUP
# Expose the port the server will run on (5075, 5076, 5077).
EXPOSE 5075-5077

# Copy the project into the image.
COPY . /app

# Sync the project into the new environment, asserting the lockfile is up to date.
WORKDIR /app
RUN uv sync --locked --no-editable --no-dev --package ljm-source

# Run the server.
ENTRYPOINT ["src/sources/ljm/docker_entrypoint.sh"]
