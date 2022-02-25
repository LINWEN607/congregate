#!/bin/bash

# Congregate - GitLab instance migration utility 
#
# Copyright (c) 2021 - GitLab
#
# Master script for running congregate
#

# We are trapping ctrl+c to help clean up any dangling PIDs on a forced quit
trap rm_pid INT TERM QUIT

function rm_pid() {
    rm -f /tmp/congregate.pid
}

function is_running() {
    check="$(ps aux | grep -v grep | grep $(cat /tmp/congregate.pid))"
        if [[ ! -z "$check" ]]; then
            return 0
        else
            return 1
        fi
}

function do_it() {
    set -e
    CONGREGATE_PATH=$(pwd) APP_PATH=$(pwd) && poetry run python congregate/main.py $@
    exit_code=$?
    if [ "${exit_code}" -ne 0 ]; then
        echo "exit ${exit_code}"
    fi
    echo "echo 0"
    set +e
}

if [ ! -f "/tmp/congregate.pid" ]; then
    echo $$ > /tmp/congregate.pid
    if [[ -z ${CONGREGATE_PATH+x} ]]; then
        echo "CONGREGATE_PATH not set. Defaulting to current directory: ($(pwd))"
        do_it $@
    else
        cd ${CONGREGATE_PATH}
        do_it $@
    fi
else
    if is_running; then
        echo "Congregate is already running with pid '$(cat /tmp/congregate.pid)'."
        echo "Exiting"
        exit
    else
        echo "Congregate was listed as running using pid '$(cat /tmp/congregate.pid)', but no such process exists."
        echo "Will delete the pid file, and retry."
        echo $$ > /tmp/congregate.pid
        do_it $@
    fi
fi

if [ -f "/tmp/congregate.pid" ]; then
    rm_pid
fi