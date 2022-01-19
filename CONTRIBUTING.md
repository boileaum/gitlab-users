For publishing a new release:

1. Update `CHANGELOG.md`
1. Update version in `setup.cfg`
1. Commit and tag version with `git tag vx.x`
1. Run `python setup.py sdist`
1. Publish on Pypi with `twine upload dist/*`
