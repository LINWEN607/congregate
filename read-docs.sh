#!/bin/bash

poetry run sphinx-apidoc -f -o congregate/docs/source/ ./
cd congregate/docs
make html
cd build/html
echo "Loading doc site"

python_version=$(python --version | awk '{print $2}')

if [[ "$python_version" == *"3"* ]]; then
    python -m http.server
else
    python3 -m http.server
fi