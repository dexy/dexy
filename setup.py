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
            'Markdown',
            'PyYAML',
            'chardet',
            'dexy_viewer',
            'docutils',
            'inflection>=0.0.2',
            'jinja2',
            'pexpect',
            'ply>=3.4',
            'pygments',
            'python-modargs>=1.7',
            'requests>=0.10.6'
            ],
        name='dexy',
        packages=find_packages(),
        url='http://dexy.it',
        version=DEXY_VERSION
        )
