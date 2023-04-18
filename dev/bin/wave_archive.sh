#!/bin/bash

echo "What is the Wave Name that was ran, that we should be cleaning up?"
read WAVE_NAME

printf "\n*********    Creating required directories    *********\n\n"

mkdir -pv $CONGREGATE_PATH/data/waves/$WAVE_NAME/{logs,results,diff,staged,listing}

mkdir -pv "$CONGREGATE_PATH/data/archive"

printf "\n*********    Moving Logs, Staged, and Results Data    *********\n\n"

mv $CONGREGATE_PATH/data/logs/* $CONGREGATE_PATH/data/waves/$WAVE_NAME/logs/
mv $CONGREGATE_PATH/data/results/* $CONGREGATE_PATH/data/waves/$WAVE_NAME/results/
mv $CONGREGATE_PATH/data/staged_*.json $CONGREGATE_PATH/data/waves/$WAVE_NAME/staged/

printf "\n*********    Copying Listing Data and any CSV - XLS    *********\n\n"

cp $CONGREGATE_PATH/data/{users,groups,projects}.json $CONGREGATE_PATH/data/waves/$WAVE_NAME/listing/
cp $CONGREGATE_PATH/data/*.csv $CONGREGATE_PATH/data/waves/$WAVE_NAME/listing/
cp $CONGREGATE_PATH/data/*.xls $CONGREGATE_PATH/data/waves/$WAVE_NAME/listing/

printf "\n*********    Compressing data to $CONGREGATE_PATH/data/archive/$WAVE_NAME.tar.gz    *********\n\n"

tar cvfz $CONGREGATE_PATH/data/archive/$WAVE_NAME.tar.gz -C $CONGREGATE_PATH/data/waves $WAVE_NAME
