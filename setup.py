from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="gitlab-users",
    version="0.3",
    packages=find_packages(),
    entry_points={
        'console_scripts': ['gitlab-users = gitlab_users.gitlab_users:main'],
                 },
    package_data={},

    # metadata for upload to PyPI
    author="Matthieu Boileau",
    author_email="matthieu.boileau@math.unistra.fr",
    description=("Export GitLab users information and automate user "
                 "accounts creation"),
    install_requires=['python-gitlab>0.20'],
    license="MIT",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Environment :: Console',
        'Intended Audience :: System Administrators',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
    ],
    keywords="gitlab API CLI",
    url="https://gitlab.math.unistra.fr/gitlab-tools/gitlab-users",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
    long_description=long_description
)
