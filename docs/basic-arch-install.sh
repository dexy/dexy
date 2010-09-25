set -o errexit #  exit this script if an error occurs
stime=$(date '+%s')
echo "starting install at `date`"
pacman -Sy --noconfirm python
pacman -Sy --noconfirm mercurial
pacman -Sy --noconfirm setuptools

# Packages Used by Dexy
easy_install nose
easy_install ordereddict # only needed if your python < 2.7
easy_install simplejson
easy_install pydot

# Basic packages for handlers/examples
easy_install jinja2
easy_install pexpect
easy_install pygments
easy_install http://dexy.it/tmp/idiopidae-0.5.tgz
easy_install http://dexy.it/tmp/zapps-0.5.tgz
pacman -Sy --noconfirm r

# Things useful to have for development
pacman -Sy --noconfirm vim
pacman -Sy --noconfirm screen
pacman -Sy --noconfirm openssh

hg clone http://bitbucket.org/ananelson/dexy

cd dexy/
mkdir artifacts
mkdir logs
nosetests
python setup.py install
cd ..

echo "completed install at `date`"
etime=$(date '+%s')
echo "elapsed time is $((($etime-$stime)/60)) minutes"
