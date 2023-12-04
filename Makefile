
.PHONY: python_version venv format help

MIN_PYTHON_VERSION := 3.10
PYTHON_EXECUTABLE := $(shell which python)

python_version:
	@if [ -z "$(PYTHON_EXECUTABLE)" ]; then \
		echo "Error: Python executable not found."; \
		exit 1; \
	fi
	@PYTHON_VERSION=$$($(PYTHON_EXECUTABLE) --version); \
	if [ "$$PYTHON_VERSION" \< "$(MIN_PYTHON_VERSION)" ]; then \
		echo "Error: Python version $(MIN_PYTHON_VERSION) or higher is required."; \
		exit 1; \
	fi 


# Set the virtual environment activation command based on the OS
ifdef SystemRoot  # Check if running on Windows
	VENV_ACTIVATE := venv\Scripts\activate
else
	VENV_ACTIVATE := source venv/bin/activate
endif

venv:
	@echo "Activating virtual environment..."
	@$(VENV_ACTIVATE)

	@echo "Upgrading pip..."
	@pip install --upgrade pip

	@echo "Installing wheel..."
	@pip install wheel

	@echo "Installing Python dependencies for Omnibus..."
	@pip install -r requirements.txt

	@echo "Installing Python dependencies for sources/ni/..."
	@cd sources/ni && pip install -r requirements.txt

	@echo "Installing Python dependencies for sources/parsley/..."
	@cd sources/parsley && pip install -r requirements.txt

	@echo "Installing Python dependencies for sinks/dashboard/..."
	@cd sinks/dashboard && pip install -r requirements.txt

	@echo "Installing Omnibus library locally..."
	@pip install -e .

	@echo "Initializing Parsley submodule..."
	@git submodule update --init --recursive

	@echo "Installing Parsley library locally..."
	@pip install -e ./parsley

format:
	@bash tools/format.sh

help:
	@echo "Available commands:"
	@echo "  make venv    - Set up the virtual environment and install dependencies"
	@echo "  make format  - Run the format.sh script"
	@echo "  make help    - Display this help message"
