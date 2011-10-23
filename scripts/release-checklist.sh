echo "running pyflakes"
pyflakes dexy

set -e

echo "Checking if all changes have been committed to git and pushed..."


if git diff --quiet HEAD; then
    echo "ok"
else
    echo "there are unadded changes! stopping!"
    exit
fi

if git diff --quiet --staged; then
    echo "ok"
else
    echo "there are uncommitted changes! stopping!"
    exit
fi

if git diff --quiet HEAD remotes/origin/HEAD; then
    echo "ok"
else
    echo "there are unpushed changes! stopping!"
    exit
fi

if git pull; then
    echo "ok"
else
    echo "an error occurred when pulling changes from remote repo"
    exit
fi

echo "run nose tests"
if ! nosetests; then
    echo "tests failed!"
    exit
fi

echo "running venvtest"
./scripts/venvtest

echo "success!"

echo "now run ~/.ec2/release-dexy.sh script"
echo "then tag release in git e.g. 'git tag 0.4.1'"
echo "note *all* projects should be tagged"
echo "then bump version in repo and commit"
echo "push to remote git repo"
echo "then generate website and upload"

