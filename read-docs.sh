#!/bin/sh

pipenv run generate-docs
cd congregate/docs
make html
cd build/html
echo "Loading doc site"
python -m SimpleHTTPServer