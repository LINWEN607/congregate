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
    ${CONGREGATE_PATH}/user_cleanup.sh
fi

if [ ! -f ${CONGREGATE_PATH}/data/groups.json ]; then
    ${CONGREGATE_PATH}/group_cleanup.sh
fi

${CONGREGATE_PATH}/stage_projects.sh all

${CONGREGATE_PATH}/migrate_projects.sh