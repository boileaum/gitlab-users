## Version 1.0.3 - 2025-06-02

### Changed

- Update dependencies to latest version of python-gitlab
- use a pyproject.toml file for packaging
- update CONTRIBUTING.md for development and release instructions

### Added

- some tests for the CLI commands
- CI pipeline with GitHub Actions

## Version 0.8.7 - 2022-09-21

- Add a `--csv` option to output csv structured data

## Version 0.8.6 - 2022-04-27

- Passing a gitlab connection to GLUser class and children is now possible

## Version 0.8.5 - 2022-01-18

- Add `--active` option for listing active users (last connection is < 1 year)
- Limit to python-gitlab < 3.0.0 for compatibility

## Version 0.8.4 - 2019-09-12

- Add a `-n, --dry-run` option for user creation and deletion

## Version 0.8.3 - 2019-08-09

- Add `--name-only` option (thanks to @jordiromera)

## Version 0.8.2 - 2019-03-28

- Use requirements.txt for project packaging

## Version 0.8.1 - 2019-03-28

- Fix missing requirement

## Version 0.8 - 2018-11-17

- Fix --delete-from error with python2
- Enable to remove unnecessary commas in newusers.csv file (thanks to @yangliping)

## Version 0.7 - 2018-09-05

- Handle gitlab subgroups

## Version 0.6 - 2018-07-06

- Handle gitlab subgroups

## Version 0.5 - 2017-10-24

- Fix bugs with printing to stdout

## Version 0.4 - 2017-10-11

- Compatibility with python2
- Fix bugs with -u and -g options

## Version 0.3 - 2017-06-12

- Handle non default GitLab instance target (#3)
- Add a `--sign-in` argument to list users who have already signed in (!1)
- Fix incompatible filters (!1)

## Version 0.3 - 2017-06-12

- essentially packaging work
