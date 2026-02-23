<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Building the Hamilton UI

The Hamilton UI has two deployment modes, each with its own build process:

## 1. Mini Mode (PyPI Package Distribution)

In "mini mode," the frontend React application is built and bundled directly into the `apache-hamilton-ui` Python package. The Django backend serves the static assets from the `build/` directory. This is the simplest deployment model - a single pip install that includes everything.

### Building for Mini Mode

#### Build UI Assets

```bash
# From the repository root
hamilton-admin-build-ui
```

This command:
1. Installs npm dependencies (`npm install`)
2. Builds the React frontend (`npm run build`)
3. Copies built assets to `ui/backend/server/build/`
4. Verifies the build succeeded

**For faster iteration** (skip npm install):
```bash
hamilton-admin-build-ui --skip-install
```

#### Build and Publish to PyPI

```bash
# Build UI and publish to TestPyPI
hamilton-admin-build-and-publish

# Build UI and publish to PyPI (production)
hamilton-admin-build-and-publish --prod
```

This command:
1. Builds the UI (calls `hamilton-admin-build-ui`)
2. Navigates to `ui/backend/`
3. Runs `python -m build` to create wheel and sdist
4. Publishes to PyPI using `twine`

#### Manual Build Process

If you prefer to build manually:

```bash
# 1. Build frontend
cd ui/frontend
npm install
npm run build

# 2. Copy to backend
rm -rf ../backend/server/build
mkdir -p ../backend/server/build
cp -a build/. ../backend/server/build/

# 3. Build Python package
cd ../backend
python -m build

# 4. Verify package contents
tar -tzf dist/apache-hamilton-ui-*.tar.gz | grep build/

# 5. Publish (optional)
python -m twine upload --repository testpypi dist/*
```

### Running Mini Mode

After installation, start the UI server:

```bash
pip install apache-hamilton-ui
hamilton ui --port 8241
```

Navigate to `http://localhost:8241` to access the UI.

### How Mini Mode Works

**Django Configuration** (`ui/backend/server/server/settings.py`):
- When `HAMILTON_ENV=mini`, Django serves static files from `build/static/`
- The `MEDIA_ROOT` is set to `build/` for public assets
- Catch-all route serves `index.html` for client-side routing

**Package Configuration** (`ui/backend/pyproject.toml`):
- `[tool.flit.sdist]` includes `hamilton_ui/build/**` to bundle assets
- Built assets are packaged in the wheel/sdist distributions

---

## 2. Docker Mode (Container Deployment)

In "Docker mode," the frontend and backend run as separate containers. Nginx serves the frontend, and the Django backend provides the API. This is the recommended approach for production deployments and local development.

### Building for Docker Mode

#### Development Build

```bash
cd ui
./dev.sh --build
```

This builds and runs:
- **Frontend**: React dev server at `http://localhost:8242`
- **Backend**: Django dev server at `http://localhost:8241`
- **PostgreSQL**: Database at `localhost:5432`

Features:
- Live code reloading via volume mounts
- Verbose logging
- Local auth (no external services)

#### Production Build

```bash
cd ui
./run.sh --build
```

This builds and runs:
- **Frontend**: Nginx serving optimized React build at `http://localhost:8242`
- **Backend**: Gunicorn serving Django at `http://localhost:8241`
- **PostgreSQL**: Database at `localhost:5432`

Features:
- Immutable containers (no volume mounts)
- Optimized builds
- Production-ready configuration

#### Multi-Architecture Build & Push

```bash
cd ui
./buildx_and_push.sh
```

This:
1. Fetches the latest version from PyPI
2. Builds Docker images for both `amd64` and `arm64`
3. Pushes to Docker Hub:
   - `dagworks/ui-frontend:VERSION` and `dagworks/ui-frontend:latest`
   - `dagworks/ui-backend:VERSION` and `dagworks/ui-backend:latest`

### Stopping Docker Containers

```bash
cd ui
./stop.sh
```

### Docker Architecture

```
┌─────────────────────────────────────────────┐
│           Hamilton UI (Docker Mode)          │
├─────────────────────────────────────────────┤
│                                               │
│  Frontend Container (Nginx)                  │
│  ├── Port: 8242                              │
│  ├── Serves: React app (static assets)       │
│  └── Proxies: /api → backend:8241           │
│                                               │
│  Backend Container (Django)                  │
│  ├── Port: 8241                              │
│  ├── API: /api/                              │
│  └── Database: PostgreSQL                    │
│                                               │
│  PostgreSQL Container                        │
│  └── Port: 5432                              │
│                                               │
└─────────────────────────────────────────────┘
```

---

## Comparison: Mini Mode vs Docker Mode

| Feature | Mini Mode | Docker Mode |
|---------|-----------|-------------|
| **Deployment** | Single pip install | Docker Compose |
| **Frontend Serving** | Django static files | Nginx (production) or dev server |
| **Build Complexity** | Simple | More complex |
| **Use Case** | Quick demos, simple deployments | Development, production deployments |
| **Scalability** | Limited | Easily scalable |
| **Hot Reload** | No | Yes (dev mode) |
| **Database** | SQLite or external | PostgreSQL (included) |

---

## Build Script Architecture

The build process follows the pattern from Apache Burr's UI build system:

### Build Script (`ui/admin.py`)

```python
def _build_ui(skip_install: bool = False):
    """Build the UI from source following Burr's pattern."""
    # 1. npm install (unless --skip-install)
    # 2. npm run build
    # 3. rm -rf backend/server/build
    # 4. mkdir -p backend/server/build
    # 5. cp -a frontend/build/. backend/server/build/
    # 6. Verify critical files exist
```

### CLI Entry Points (`pyproject.toml`)

```toml
[project.scripts]
hamilton-admin-build-ui = "ui.admin:build_ui"
hamilton-admin-build-and-publish = "ui.admin:build_and_publish"
```

---

## Troubleshooting

### Build Verification Failed

If you see "Build failed: index.html not found" or "Build failed: static/ directory not found":

1. Check that the frontend build succeeded: `ls ui/frontend/build/`
2. Verify npm dependencies are installed: `ls ui/frontend/node_modules/`
3. Try a clean build:
   ```bash
   cd ui/frontend
   rm -rf build node_modules
   npm install
   npm run build
   ```

### Package Doesn't Include Assets

If the built package doesn't include frontend assets:

1. Verify `pyproject.toml` includes `hamilton_ui/build/**`:
   ```bash
   grep -A 5 "\[tool.flit.sdist\]" ui/backend/pyproject.toml
   ```
2. Check package contents:
   ```bash
   tar -tzf ui/backend/dist/apache-hamilton-ui-*.tar.gz | grep build/
   ```

### Docker Build Issues

If Docker builds fail:

1. Ensure Docker is running: `docker ps`
2. Check Docker Compose is available: `docker compose version`
3. Clear old containers: `cd ui && ./stop.sh`
4. Rebuild from scratch: `cd ui && ./dev.sh --build`

---

## References

- **Burr's build pattern**: `~/salesforce/burr/burr/cli/__main__.py:135-156`
- **Django mini mode settings**: `ui/backend/server/server/settings.py:147-154`
- **Django URL configuration**: `ui/backend/server/server/urls.py:44-52`
- **Flit packaging config**: `ui/backend/pyproject.toml`
