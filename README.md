# gitlab-users

[![CI](https://github.com/boileaum/gitlab-users/actions/workflows/ci-publish.yml/badge.svg)](https://github.com/boileaum/gitlab-users/actions/workflows/ci-publish.yml)
[![Latest Release](https://img.shields.io/github/v/release/boileaum/gitlab-users?label=release)](https://github.com/boileaum/gitlab-users/releases)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Doc](https://img.shields.io/badge/doc-sphinx-blue)](https://boileaum.github.io/gitlab-users/)

A CLI and an API to manage GitLab user accounts, based on [python-gitlab](https://github.com/python-gitlab/python-gitlab).

## Features

- List users and groups from a GitLab instance
- Export users to CSV
- Bulk create/delete users from CSV
- Export SSH keys

## Installation

```sh
pip install gitlab-users
```

Requires Python 3.9+ and a valid `python-gitlab` configuration (`~/.python-gitlab.cfg`).

## Usage

Get help and list all commands:
```sh
gitlab-users -h
```

List all users:
```sh
gitlab-users list-users
```

List all groups:
```sh
gitlab-users list-groups
```

Export all users to a CSV file:
```sh
gitlab-users export-users users.csv
```

Create users from a CSV file (see example format below):
```sh
gitlab-users create-from-csv users.csv
```

Delete users from a CSV/text file (usernames in first column):
```sh
gitlab-users delete-from-csv users.csv
```

Delete a single user (asks for confirmation):
```sh
gitlab-users delete-user USERNAME
```

Export SSH keys of a user:
```sh
gitlab-users export-ssh-keys USERNAME
```

### Example CSV format

```text
# username, name, email, [organization], [location], [group], [access_level]
# Note: The fields in square brackets are optional and can be omitted if not needed.
ww,Diana Prince,wonder.woman@themyscira.org,,Themyscira
wayne,Bruce Wayne,bruce.wayne@wayne-enterprises.com,Wayne Enterprises,Gotham City,board,owner
```

## Development

- See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, linting, testing, and release instructions.
- Run all tests: `pytest`
- Lint and format: `ruff check .` and `black .`

## Documentation

- Full API and usage documentation: [Sphinx HTML docs](https://boileaum.gitlab-users.pages.gitlab-tools/docs/)
- To build locally:
  ```sh
  cd docs
  make html
  ```

## License

MIT License
