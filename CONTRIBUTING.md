
# Contributing & Releasing

## Development

- Use a recent Python (>=3.8 recommended).
- Install development dependencies:
  ```bash
  pip install -e .[dev]
  ```
- Run code quality checks:
  ```bash
  ruff check .
  black --check .
  pytest
  ```

## Publishing a new release

1. Update `CHANGELOG.md` and bump the version in `pyproject.toml` and `src/gitlab_users/__init__.py`.
2. Commit and tag the release:
   ```bash
   git add .
   git commit -m "Release vX.Y.Z"
   git tag vX.Y.Z
   git push && git push --tags
   ```
3. The GitHub Actions workflow will automatically build and publish the package to PyPI when a tag `v*` is pushed to `main`/`master`.

Manual build/publish (optional):
```bash
python -m build
twine upload dist/*
```
