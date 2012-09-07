from setuptools import setup, find_packages
import dexy

setup(
        author='Ana Nelson',
        author_email='ana@ananelson.com',
        classifiers=[
            "Development Status :: 4 - Beta",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "Intended Audience :: Education",
            "Intended Audience :: Financial and Insurance Industry",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Topic :: Documentation",
            "Topic :: Software Development :: Build Tools",
            "Topic :: Software Development :: Code Generators",
            "Topic :: Software Development :: Documentation",
            "Topic :: Text Processing",
            "Topic :: Text Processing :: Markup :: HTML",
            "Topic :: Text Processing :: Markup :: LaTeX"
            ],
        dependency_links = [ "http://dexy.it/external-dependencies/" ],
        description='Document Automation',
        entry_points = {
            'console_scripts' : [
                'dexy = dexy.commands:run',
                'screenshot = dexy.screenshot:run',
                'ppjson = dexy.ppjson:run'
                ]
            },
        include_package_data = True,
        install_requires = [
            'idiopidae>=0.5.2',
            'jinja2',
            'nose',
            'pexpect',
            'pygments',
            'python-modargs>=1.4',
            'requests>=0.10.6',
            'web.py>=0.3', # for viewer
            'zapps'
            ],
        name='dexy',
        packages=find_packages(),
        package_data = { "dexy" : ["ext/*"] },
        url='http://dexy.it',
        version=dexy.__version__
        )

