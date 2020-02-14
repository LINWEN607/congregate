#!/bin/bash

# Congregate - GitLab instance migration utility 
#
# Copyright (c) 2020 - GitLab
#
# Master script for running congregate
#

if [[ -z ${CONGREGATE_PATH+x} ]]; then
    echo "CONGREGATE_PATH not set. Defaulting to current directory: ($(pwd))"
    CONGREGATE_PATH=$(pwd) poetry run python congregate/main.py $@
else
    cd ${CONGREGATE_PATH}
    poetry run python congregate/main.py $@
fi
