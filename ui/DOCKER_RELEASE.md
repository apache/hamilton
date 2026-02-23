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

# Apache Hamilton UI - Docker Release Guide

This document describes the Apache-compliant Docker build and release process for Hamilton UI.

## Overview

Hamilton UI provides three Docker deployment modes:

1. **Development Mode** (`dev.sh`) - Hot-reload development with separate frontend/backend containers
2. **Production Mode** (`run.sh`) - Production-ready with separate frontend/backend containers
3. **Official Release** (`buildx_and_push.sh`) - Multi-architecture builds for Apache Docker Hub

## Apache Software Foundation Requirements

As an Apache Incubator project, Hamilton must follow ASF Docker distribution policies:

### 1. Docker Hub Namespace

All official Docker images MUST be published to:
- ✅ `apache/hamilton-ui-frontend`
- ✅ `apache/hamilton-ui-backend`
- ❌ NOT `dagworks/*` or personal namespaces

### 2. Incubator Disclaimer

All Dockerfiles and Docker Hub overview pages MUST include:

```
Apache Hamilton is an effort undergoing incubation at The Apache Software
Foundation (ASF), sponsored by the Apache Incubator. Incubation is required
of all newly accepted projects until a further review indicates that the
infrastructure, communications, and decision making process have stabilized
in a manner consistent with other successful ASF projects. While incubation
status is not necessarily a reflection of the completeness or stability of
the code, it does indicate that the project has yet to be fully endorsed by
the ASF.
```

### 3. Tagging Policy

The `:latest` tag can ONLY be used for PMC-approved releases:

| Build Type | Tag Format | Can Use `:latest`? | Example |
|------------|------------|-------------------|---------|
| Release | `VERSION` | ✅ Yes (with PMC approval) | `0.0.17` |
| Release Candidate | `VERSION-rcN` | ❌ No | `0.0.18-rc1` |
| Snapshot | `VERSION-SNAPSHOT` | ❌ No | `0.0.18-SNAPSHOT` |
| Nightly | `VERSION-nightly-YYYYMMDD` | ❌ No | `0.0.18-nightly-20260223` |

### 4. License and Notice Files

Docker images SHOULD include:
- `LICENSE` - Apache License 2.0
- `NOTICE` - Copyright and third-party notices
- `DISCLAIMER` - Incubator disclaimer

## Development Workflow

### Local Development (`dev.sh`)

For active development with hot-reload:

```bash
cd ui
./dev.sh --build

# Access at:
# - Frontend: http://localhost:8242
# - Backend API: http://localhost:8241
# - PostgreSQL: localhost:5432
```

**Features:**
- Hot-reload for both frontend and backend
- Source code mounted as volumes
- Development-optimized (not production-ready)
- Single architecture (your host platform)

### Local Production Testing (`run.sh`)

To test production builds locally:

```bash
cd ui
./run.sh --build

# Access at:
# - Frontend: http://localhost:8242
# - Backend API: http://localhost:8241
```

**Features:**
- Production-optimized builds
- No hot-reload
- Nginx serves frontend static files
- Single architecture (your host platform)

## Official Release Process

### Prerequisites

1. **Docker Buildx** installed and configured:
   ```bash
   docker buildx version
   ```

2. **Docker Hub credentials** with push access to `apache/hamilton-*`:
   ```bash
   docker login
   ```

3. **PMC approval** for releases (required before tagging `:latest`)

### Building Release Candidates

Release candidates are used for community voting before official releases:

```bash
cd ui
./buildx_and_push.sh --version 0.0.18 --type rc --rc-number 1
```

This creates:
- `apache/hamilton-ui-frontend:0.0.18-rc1`
- `apache/hamilton-ui-backend:0.0.18-rc1`

### Building Official Releases

After PMC approval, build and tag the official release:

```bash
cd ui
./buildx_and_push.sh --version 0.0.17 --type release --tag-latest
```

**Interactive Prompt:**
```
WARNING: You are about to tag this build as :latest
This should ONLY be done for PMC-approved releases.

Has this release been approved by the Apache Hamilton PMC? (yes/no):
```

Type `yes` to proceed. This creates:
- `apache/hamilton-ui-frontend:0.0.17`
- `apache/hamilton-ui-frontend:latest`
- `apache/hamilton-ui-backend:0.0.17`
- `apache/hamilton-ui-backend:latest`

### Building Snapshots

For development snapshots (not official releases):

```bash
cd ui
./buildx_and_push.sh --version 0.0.18 --type snapshot
```

This creates:
- `apache/hamilton-ui-frontend:0.0.18-SNAPSHOT`
- `apache/hamilton-ui-backend:0.0.18-SNAPSHOT`

### Building Nightly Builds

For automated nightly builds:

```bash
cd ui
./buildx_and_push.sh --version 0.0.18 --type nightly
```

This creates:
- `apache/hamilton-ui-frontend:0.0.18-nightly-20260223`
- `apache/hamilton-ui-backend:0.0.18-nightly-20260223`

Date is automatically appended (format: YYYYMMDD).

## Multi-Architecture Support

All official builds use Docker Buildx to create multi-architecture images:

**Platforms:**
- `linux/amd64` (Intel/AMD x86-64)
- `linux/arm64` (Apple Silicon, ARM servers)

**Build Process:**
1. Creates `hamilton-builder` buildx instance (if not exists)
2. Builds both architectures in parallel
3. Pushes manifest list to Docker Hub
4. Users automatically pull correct architecture

## Docker Hub Setup

### Repository Overview Text

Both `apache/hamilton-ui-frontend` and `apache/hamilton-ui-backend` repositories MUST include:

```markdown
# Apache Hamilton UI

Apache Hamilton is an effort undergoing incubation at The Apache Software
Foundation (ASF), sponsored by the Apache Incubator. Incubation is required
of all newly accepted projects until a further review indicates that the
infrastructure, communications, and decision making process have stabilized
in a manner consistent with other successful ASF projects. While incubation
status is not necessarily a reflection of the completeness or stability of
the code, it does indicate that the project has yet to be fully endorsed by
the ASF.

## Quick Start

Frontend:
```bash
docker run -p 8242:8242 apache/hamilton-ui-frontend:latest
```

Backend (requires PostgreSQL):
```bash
docker run -p 8241:8241 \
  -e HAMILTON_POSTGRES_HOST=your-postgres-host \
  -e HAMILTON_POSTGRES_DB=your-db-name \
  -e HAMILTON_POSTGRES_USER=your-user \
  -e HAMILTON_POSTGRES_PASSWORD=your-password \
  apache/hamilton-ui-backend:latest
```

## Documentation

- [GitHub Repository](https://github.com/apache/hamilton)
- [Documentation](https://hamilton.apache.org/)
- [Docker Compose Examples](https://github.com/apache/hamilton/tree/main/ui)

## License

Apache License 2.0 - See [LICENSE](https://github.com/apache/hamilton/blob/main/LICENSE)
```

### Automated Builds

Consider setting up Docker Hub automated builds:

1. Link GitHub repository to Docker Hub
2. Configure build rules for tags matching `v*`
3. Ensure builds use Apache namespace and proper tagging

## Release Checklist

Before creating an official release:

- [ ] Update version in `ui/frontend/package.json`
- [ ] Update version in `ui/backend/pyproject.toml`
- [ ] Test using `./run.sh --build` locally
- [ ] Verify all tests pass
- [ ] Create release candidate: `./buildx_and_push.sh --version X.Y.Z --type rc --rc-number 1`
- [ ] Send RC to dev@hamilton.apache.org for voting
- [ ] Wait for PMC approval (72 hours minimum, 3 +1 votes from PMC members)
- [ ] Build official release: `./buildx_and_push.sh --version X.Y.Z --type release --tag-latest`
- [ ] Verify images on Docker Hub
- [ ] Announce release on dev@hamilton.apache.org
- [ ] Update documentation with new version

## Common Issues

### "Has this release been approved by the Apache Hamilton PMC?"

This prompt appears when using `--tag-latest`. Only type `yes` if:
1. A vote thread was sent to dev@hamilton.apache.org
2. At least 72 hours have passed
3. At least 3 PMC members voted +1
4. No -1 (veto) votes

### "Error: Docker Buildx is not installed"

Install Docker Buildx:
```bash
# macOS/Linux with Docker Desktop
docker buildx version

# Linux without Docker Desktop
DOCKER_BUILDKIT=1 docker build --help | grep buildx
```

### Build fails with "permission denied"

Ensure you're logged into Docker Hub with apache/* push access:
```bash
docker login
```

### "Error: --rc-number is required for release candidate builds"

When building RCs, you must specify the RC number:
```bash
./buildx_and_push.sh --version 0.0.18 --type rc --rc-number 1
```

## Security Considerations

### Current State (Development)

Current Docker setup uses:
- Root user (not production-ready)
- Django development server (not production-ready)
- Hardcoded credentials in docker-compose files (development only)

### Future Improvements

For production deployments, consider:
- Running as non-root user (UID 1000)
- Using gunicorn instead of `manage.py runserver`
- Using secrets management (Docker secrets, Kubernetes secrets)
- Adding health checks to docker-compose
- Adding .dockerignore files

## Additional Resources

- [Apache Release Policy](https://www.apache.org/legal/release-policy.html)
- [Apache Incubator Releases](https://incubator.apache.org/policy/incubation.html#releases)
- [Hamilton UI Documentation](https://hamilton.apache.org/en/latest/concepts/ui/)
