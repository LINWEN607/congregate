#!/bin/bash

mkdir congregate-${CI_COMMIT_TAG}
cp -r cli congregate-${CI_COMMIT_TAG}
cp -r helpers congregate-${CI_COMMIT_TAG}
cp -r migration congregate-${CI_COMMIT_TAG}
cp -r js-packages congregate-${CI_COMMIT_TAG}
cp -r ui congregate-${CI_COMMIT_TAG}
cp -r other congregate-${CI_COMMIT_TAG}
cp *.py congregate-${CI_COMMIT_TAG}
cp congregate congregate-${CI_COMMIT_TAG}
cp Pipfile* congregate-${CI_COMMIT_TAG}
tar -czvf congregate-${CI_COMMIT_TAG}.tar.gz congregate-${CI_COMMIT_TAG}