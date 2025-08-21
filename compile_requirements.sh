#!/bin/bash

echo "Updating requirements.txt"
uv sync
uv pip compile pyproject.toml --all-extras -o requirements.txt >/dev/null
echo "-e ." >>requirements.txt
echo "Successfully updated requirements.txt"
