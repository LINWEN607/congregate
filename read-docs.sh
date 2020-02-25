#!/bin/sh

poetry run sphinx-apidoc -f -o congregate/docs/source/ ./
cd congregate/docs
make html
cd build/html
echo "Loading doc site"
python -m SimpleHTTPServer