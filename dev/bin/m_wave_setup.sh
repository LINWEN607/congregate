#!/bin/bash

echo "What is the Wave Name we will be running?"
read WAVE_NAME

mkdir -pv $CONGREGATE_PATH/data/waves/$WAVE_NAME/{logs,results,diff,staged,listing}

mkdir -pv "$CONGREGATE_PATH/data/archive"

printf "**************************************************"
printf "********** Possible Follow Up Tasks **************"
printf "**************************************************"

cat $CONGREGATE_PATH/dev/bin/m_wave_setup.sh

## STAGE-WAVE
# "congregate stage-wave $WAVE_NAME > data/waves/$WAVE_NAME/stage_$WAVE_NAME_dry-run.log 2>&1 &"
# "congregate stage-wave $WAVE_NAME --commit > data/waves/$WAVE_NAME/stage_$WAVE_NAME.log 2>&1 &"

## MIGRATE
# nohup congregate migrate --skip-users --skip-group-import --skip-group-export > data/waves/$WAVE_NAME/migration_dry-run.log 2>&1 &
# nohup congregate migrate --skip-users --skip-group-import --skip-group-export --commit > data/waves/$WAVE_NAME/migration.log 2>&1 &

# Here are some verification samples
# 'grep -nri "^$WAVE_NAME" data/sw-customer-supplied.csv | wc -l'
# "jq '.[].name' data/staged_projects.json | wc -l "

