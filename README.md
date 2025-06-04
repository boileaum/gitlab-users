# gitlab-users

[![pipeline status](https://github.com/boileaum/gitlab-users/actions/workflows/test.yml/badge.svg)](https://github.com/boileaum/gitlab-users/actions)
[![Latest Release](https://img.shields.io/github/v/release/boileaum/gitlab-users?label=release)](https://github.com/boileaum/gitlab-users/releases)
[![Doc](https://img.shields.io/badge/doc-sphinx-blue)](https://boileaum.gitlab-users.pages.gitlab-tools/docs/)

A simple command line interface to manage GitLab user accounts, based on [python-gitlab](https://github.com/python-gitlab/python-gitlab).

## Installation

* Install the package on your system

```sh
pip install gitlab-users
```

* Edit the `~/.python-gitlab.cfg` following the [python-gitlab package instructions](http://python-gitlab.readthedocs.io/en/stable/cli.html) to setup the GitLab instance to connect with (present version only targets default instance).

## Usage

* Get help

```sh
gitlab-users -h
```

* List all users with their email

```sh
gitlab-users
```

* List emails from a given group

```sh
gitlab-users -g a_group --email-only
```

* Create multiple user accounts at once from a csv file

```sh
gitlab-users --create-from example.csv
```

where `example.csv` contains

```csv
# username, name, email, [organization], [location], [group], [access_level]
wayne,Bruce Wayne,bruce.wayne@wayne-entreprises.com,Wayne Entreprises,Gotham City,Board,owner
kent,Clark Kent,clark.kent@krypton.univ,,Smallville
```

* List unused accounts (never sign-in or last connection is older than 1 year)

```sh
gitlab-users --unused
```
