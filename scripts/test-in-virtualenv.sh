#!/bin/bash -e
TIMESTAMP=`date +%s`
TEST_DIR="/tmp/test-dexy/$TIMESTAMP"
echo "Running in $TEST_DIR"
mkdir -p $TEST_DIR
pushd $TEST_DIR
git clone ~/dev/dexy $TEST_DIR/dexy
virtualenv testenv
source testenv/bin/activate
cd dexy
pip install .
nosetests
cd docs
dexy setup
dexy
