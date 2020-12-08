#!/bin/bash

# Syntax error checking script
# 
# This script leverages pylint to check for any syntax errors

# Run pylint without searching for syntax warnings, refactor suggestions, and code coventions, 
#   do not include the pylint score, 
#   and write the output to pylint.txt
poetry run pylint congregate --disable=W,R,C --score=n -j 4 | tee pylint.txt || poetry run pylint-exit

# Since we are piping the output of pylint to tee, 
# we need to extract the PIPESTATUS exit code of the first command in the chain
if [ "${PIPESTATUS[0]}" == "2" ]; then
    errors=$(cat pylint.txt | grep -e '\.py' | wc -l)
    echo "$errors syntax errors found. Please review pylint.txt to address errors."
    exit 1
else
    echo "Pylint returned no syntax errors."
    exit 0
fi