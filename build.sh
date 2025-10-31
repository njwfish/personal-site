#!/bin/bash
# Build script wrapper that uses conda environment

cd "$(dirname "$0")"

# Use conda run to execute build.py in the website-build environment
conda run -n website-build python3 build.py "$@"

