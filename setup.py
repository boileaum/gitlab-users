from setuptools import setup, find_packages
setup(
    name="gitlab-users",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': ['gitlab-users = gitlab_users:main'],
                 },
    package_data={},

    # metadata for upload to PyPI
    author="Matthieu Boileau",
    author_email="matthieu.boileau@math.unistra.fr",
    description="Export GitLab user information and create user accounts \
    using python-gitlab API",
    license="MIT",
    keywords="gitlab, API, CLI",
    url="https://gitlab.math.unistra.fr/gitlab-tools/gitlab-users",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
