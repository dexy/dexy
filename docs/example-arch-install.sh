pacman -Sy --noconfirm python
pacman -Sy --noconfirm mercurial
pacman -Sy --noconfirm setuptools

# Packages Used by Dexy
easy_install nose
easy_install ordereddict # only needed if your python < 2.7
easy_install simplejson
easy_install pydot

# Packages Used by Handlers/Examples/Tests
pacman -Sy --noconfirm r
easy_install jinja2
easy_install pexpect
easy_install pygments
easy_install http://dexy.it/tmp/idiopidae-0.5.tgz
easy_install http://dexy.it/tmp/zapps-0.5.tgz

hg clone http://bitbucket.org/ananelson/dexy
cd dexy/
mkdir artifacts
nosetests
python setup.py install

