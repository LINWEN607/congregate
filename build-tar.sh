#!/bin/bash

mkdir congregate-${CI_COMMIT_TAG}
cp -r congregate congregate-${CI_COMMIT_TAG}
cp -r js-packages congregate-${CI_COMMIT_TAG}
cp congregate.sh congregate-${CI_COMMIT_TAG}
cp Pipfile* congregate-${CI_COMMIT_TAG}
cp LICENSE congregate-${CI_COMMIT_TAG}
cp README.md congregate-${CI_COMMIT_TAG}
tar -czvf congregate-${CI_COMMIT_TAG}.tar.gz congregate-${CI_COMMIT_TAG}