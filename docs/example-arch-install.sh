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

# Packages Used by Handlers/Examples/Tests
pacman -Sy --noconfirm xorg # X11 + fonts etc for R image rendering
pacman -Sy --noconfirm r
pacman -Sy --noconfirm texlive-most
pacman -Sy --noconfirm espeak lame # for the text-to-speech example
pacman -Sy --noconfirm fftw freeglut # for the seewave graph
pacman -Sy --noconfirm clang # for nice verbose C compiling
easy_install jinja2
easy_install pexpect
easy_install pygments
easy_install http://dexy.it/tmp/idiopidae-0.5.tgz
easy_install http://dexy.it/tmp/zapps-0.5.tgz
easy_install http://pypi.python.org/packages/source/d/docutils/docutils-0.6.tar.gz
easy_install rst2beamer

# R packages to install
echo "install.packages(\"seewave\", repos=\"http://cran.r-project.org\")" | R --vanilla

# Things useful to have for development
pacman -Sy --noconfirm vim
pacman -Sy --noconfirm screen
pacman -Sy --noconfirm openssh

hg clone http://bitbucket.org/ananelson/dexy
hg clone http://bitbucket.org/ananelson/dexy-blog
hg clone http://bitbucket.org/ananelson/dexy-examples

cd dexy/
mkdir artifacts
mkdir logs
nosetests
python setup.py install
cd ..

cd dexy-blog/
mkdir artifacts
mkdir logs
cd ..

cd dexy-examples/
mkdir artifacts
mkdir logs
cd ..

echo "completed install at `date`"
etime=$(date '+%s')
echo "elapsed time is $((($etime-$stime)/60)) minutes"
