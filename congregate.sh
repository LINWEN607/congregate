#!/bin/bash

# Congregate - GitLab instance migration utility 
#
# Copyright (c) 2020 - GitLab
#
# Master script for running congregate
#

trap rm_pid INT

function rm_pid() {
    rm /tmp/congregate.pid
}

if [ ! -f "/tmp/congregate.pid" ]; then
    echo $$ > /tmp/congregate.pid
    if [[ -z ${CONGREGATE_PATH+x} ]]; then
        echo "CONGREGATE_PATH not set. Defaulting to current directory: ($(pwd))"
        CONGREGATE_PATH=$(pwd) poetry run python congregate/main.py $@
    else
        cd ${CONGREGATE_PATH}
        poetry run python congregate/main.py $@
    fi
else
    echo "Congregate is already running at $(cat /tmp/congregate.pid). Exiting"
    exit
fi

if [ -f "/tmp/congregate.pid" ]; then
    rm_pid
fi