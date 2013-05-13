from setuptools import setup, find_packages
from dexy.version import DEXY_VERSION

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
            'pygments.lexers' : [
                'rst+django = dexy.filters.utils:RstDjangoLexer'
                ],
            'console_scripts' : [
                'dexy = dexy.commands:run'
                ]
            },
        include_package_data = True,
        install_requires = [
            'PyYAML',
            'chardet',
            'dexy_viewer',
            'docutils',
            'idiopidae>=0.5.4',
            'inflection>=0.0.2',
            'jinja2',
            'ordereddict',
            'pexpect',
            'pygments',
            'python-modargs>=1.7',
            'requests>=0.10.6',
            'zapps>=0.5.1'
            ],
        name='dexy',
        packages=find_packages(),
        url='http://dexy.it',
        version=DEXY_VERSION
        )

