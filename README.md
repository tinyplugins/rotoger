# rotoger

### environment variables
ROTOGER_LOG_PATH = "./logs"
ROTGER_MAX_BYTES = 10485760
ROTOGER_BACKUP_COUNT = 5

---

### Build & Publish to PyPI

This project uses [`uv`](https://docs.astral.sh/uv/) for building and publishing.

#### Prerequisites

- Install `uv`: https://docs.astral.sh/uv/getting-started/installation/
- A [PyPI](https://pypi.org/) account with an API token (or use [TestPyPI](https://test.pypi.org/) for testing)

#### 1. Build the package

```bash
uv build
```

This will produce both a source distribution (`.tar.gz`) and a wheel (`.whl`) in the `dist/` directory.

#### 2. Publish to PyPI

```bash
uv publish
```

`uv publish` will prompt for your credentials. You can also provide a PyPI API token via the environment variable:

```bash
UV_PUBLISH_TOKEN=pypi-<your-token> uv publish
```

#### 3. Publish to TestPyPI (optional)

Use TestPyPI to verify the package before releasing to the real index:

```bash
uv publish --publish-url https://test.pypi.org/legacy/ --token pypi-<your-test-token>
```

#### Versioning

Bump the `version` field in `pyproject.toml` before each release:

```toml
[project]
version = "x.y.z"
```
