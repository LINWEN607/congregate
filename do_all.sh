#!/bin/bash

# Congregate - GitLab instance migration utility 
#
# Copyright (c) 2018 - GitLab
#
# One-liner command to handle the whole process from configuration to migration
#

if [ ! -f ${CONGREGATE_PATH}/data/config.json ]; then
    ${CONGREGATE_PATH}/config.sh
fi

if [ ! -f ${CONGREGATE_PATH}/data/users.json ]; then
    python ${CONGREGATE_PATH}/users.py --retrieve=True}
fi

if [ ! -f ${CONGREGATE_PATH}/data/groups.json ]; then
    python ${CONGREGATE_PATH}/groups.py --retrieve=True
fi

python ${CONGREGATE_PATH}/stage_projects.py all

${CONGREGATE_PATH}/migrate_projects.sh