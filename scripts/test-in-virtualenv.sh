#!/bin/bash -ev

TIMESTAMP=`date +%s`
TEST_DIR="/tmp/test-dexy/$TIMESTAMP"

echo "Running test script in $TEST_DIR"
mkdir -p $TEST_DIR
pushd $TEST_DIR

virtualenv testenv
source testenv/bin/activate

git clone ~/dev/dexy $TEST_DIR/dexy
cd dexy
pip install .
nosetests
git remote add github git@github.com:ananelson/dexy.git
cd ..

git clone ~/dev/dexy-templates $TEST_DIR/dexy-templates
cd dexy-templates
pip install .
cd ..

dexy filters
dexy reporters
dexy templates --validate

for template in `dexy templates --simple`
do
    echo ""
    echo "running template $template"
    dexy gen -d template-gen --template $template
    cd template-gen
    dexy
    dexy
    dexy -r
    cd ..
    rm -rf template-gen
done

cd dexy
git push github develop
