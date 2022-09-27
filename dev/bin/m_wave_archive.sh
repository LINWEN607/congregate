#!/bin/bash

echo "What is the Wave Name that was ran, that we should be cleaning up?"
read WAVE_NAME

# This is probably not needed if we are cleaning up after every wave.
# congregate stitch-results --result-type=project --no-of-files=10

printf "**************************************************"
printf "********** Possible Follow Up Tasks **************"
printf "**************************************************"

mv $CONGREGATE_PATH/data/logs/* $CONGREGATE_PATH/data/waves/$WAVE_NAME/logs/
mv $CONGREGATE_PATH/data/results/* $CONGREGATE_PATH/data/waves/$WAVE_NAME/results/
mv $CONGREGATE_PATH/data/staged_*.json $CONGREGATE_PATH/data/waves/$WAVE_NAME/staged/

# We should not move the following data. Odds are we need it for the next run. But we do want to save it for versioning.
cp $CONGREGATE_PATH/data/{users,groups,projects}.json $CONGREGATE_PATH/data/waves/$WAVE_NAME/listing/
cp $CONGREGATE_PATH/data/*.csv $CONGREGATE_PATH/data/waves/$WAVE_NAME/listing/

# Copied/Moved all the data, we should zip it up and get it ready for transport
tar cvfz $CONGREGATE_PATH/data/archive/$WAVE_NAME.tar.gz -C $CONGREGATE_PATH/data/waves $WAVE_NAME


# generate_diff() {
#     congregate generate-diff --staged --skip-users --skip-groups > data/waves/$WAVE_NAME/diff_$WAVE_NAME.log 2>&1
# }

# archive() {
#     mv $CONGREGATE_PATH/data/logs/* $CONGREGATE_PATH/data/waves/$WAVE_NAME/logs/
#     mv $CONGREGATE_PATH/data/results/* $CONGREGATE_PATH/data/waves/$WAVE_NAME/results/
#     mv $CONGREGATE_PATH/data/staged_*.json $CONGREGATE_PATH/data/waves/$WAVE_NAME/staged/

#     # We should not move the following data. Odds are we need it for the next run. But we do want to save it for versioning.
#     cp $CONGREGATE_PATH/data/{users,groups,projects}.json $CONGREGATE_PATH/data/waves/$WAVE_NAME/listing/
#     cp $CONGREGATE_PATH/data/*.csv $CONGREGATE_PATH/data/waves/$WAVE_NAME/listing/

#     # Copied/Moved all the data, we should zip it up and get it ready for transport
#     tar cvfz $CONGREGATE_PATH/data/archive/$WAVE_NAME.tar.gz -C $CONGREGATE_PATH/data/waves $WAVE_NAME
# }

