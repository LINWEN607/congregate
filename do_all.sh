#!/bin/bash

if [ ! -f config.json ]; then
    ./config.sh
fi

if [ ! -f users.json ]; then
    ./user_cleanup.sh
fi

if [ ! -f groups.json ]; then
    ./group_cleanup.sh
fi

./stage_projects.sh all

./migrate.sh