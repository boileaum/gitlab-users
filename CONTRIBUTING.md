For publishing a new release:

1. Update `CHANGELOG.md`
2. Update version in `setup.py`
3. Run `python setup.py sdist`
4. Publish on Pypi with `twine upload dist/*`
5. Tag version with `git tag vx.x`