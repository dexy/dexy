#!/bin/bash -ev

TIMESTAMP=`date +%s`
TEST_DIR="/tmp/test-dexy/$TIMESTAMP"

echo "Running in $TEST_DIR"
mkdir -p $TEST_DIR
pushd $TEST_DIR

virtualenv testenv
source testenv/bin/activate

git clone ~/dev/dexy $TEST_DIR/dexy
cd dexy
git remote add github git@github.com:ananelson/dexy.git

pip install .
nosetests

dexy filters
dexy reporters

for template in `dexy templates --simple` ; do
  dexy gen -d ${template}_gen --template $template
  cd ${template}_gen
  dexy
  cd ..
done

cd ../dexy
git push github develop
