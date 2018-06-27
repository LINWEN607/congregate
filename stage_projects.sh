#!/bin/bash

if [ "$1" = "all" ] || [ "$1" = "." ]; then
    echo "Adding all projects to staging environment"
else
    for project in $@
    do
        echo $project
    done
fi