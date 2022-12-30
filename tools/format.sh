#!/usr/bin/env bash

if ! type autopep8 &> /dev/null
then
    echo "Error: autopep8 is not installed."
    echo "Please run 'pip install autopep8'."
    exit 1
fi

WORKSPACE_DIR=$(git rev-parse --show-toplevel)
cd "$WORKSPACE_DIR"

autopep8 -i -r sources/ sinks/ omnibus/ tools/ --exit-code

# Check for syntax errors or undefined names
# here (F): https://flake8.pycqa.org/en/latest/user/error-codes.html
# and here (E): https://pycodestyle.pycqa.org/en/latest/intro.html#error-codes
flake8 omnibus sources sinks tools --select=E9,F63,F7,F82
