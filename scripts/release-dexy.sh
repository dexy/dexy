#!/bin/bash -ev

TIMESTAMP=`date +%s`
TEST_DIR="/tmp/test-dexy/$TIMESTAMP"

echo "Running release script in $TEST_DIR"
mkdir -p $TEST_DIR
pushd $TEST_DIR

git clone ~/dev/dexy $TEST_DIR/dexy
cd dexy

python setup.py register sdist --formats=gztar,zip upload

# Copy .tgz .zip dexy packages to external dependencies directory
cp dist/* ~/dev/dexy-site/external-dependencies/

