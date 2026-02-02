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

# Apache Hamilton UI

> A unified operational UI for managing and observing all your dataflows

The Apache Hamilton UI is a comprehensive system for monitoring, debugging, and managing Apache Hamilton dataflows throughout the entire software development lifecycle—from development to production.

## 📚 Documentation & Resources

- **[Getting Started Guide](https://hamilton.apache.org/concepts/ui)** - Complete setup and feature overview
- **[Blog Post](https://blog.dagworks.io/p/hamilton-ui-streamlining-metadata)** - In-depth introduction
- **[Quick Video Demo](https://youtu.be/0VIVSeN7Ij8?si=maeV0zdzTPSqUl1N)** - Feature walkthrough
- **[Setup Video Tutorial](https://youtu.be/DPfxlTwaNsM)** - Installation guide

---

## ✨ Key Features

The Apache Hamilton UI provides four core capabilities:

### 1. **Execution Tracking**
Track and store execution metadata in a persistent database with a server for reading, writing, and authentication.

### 2. **Data & Artifact Observability**
Monitor Apache Hamilton executions and inspect specific function results and code through an intuitive web interface.

### 3. **Lineage & Provenance**
Quickly understand how code and data are connected throughout your dataflows.

### 4. **Catalog**
Search and discover all observed dataflows with comprehensive execution history.

---

## 🎯 Feature Highlights

### Execution Tracking

<p align="center">
  <img src="./screenshots/execution_waterfall_view.png" alt="Waterfall view showing execution performance" width="30%" style="margin-right: 20px;"/>
  <img src="./screenshots/execution_graph_error.png" alt="Graph view highlighting errors" width="30%" style="margin-right: 20px;"/>
  <img src="./screenshots/execution_comparison_waterfall.png" alt="Comparing execution performance" width="30%"/>
</p>
<p align="center">
  <em>Identify bottlenecks (left) • Pinpoint errors (middle) • Compare performance (right)</em>
</p>

### Data & Artifact Observability

<p align="center">
  <img src="./screenshots/execution_data_view.png" alt="Data visualization for a run" width="30%"/>
  <img src="./screenshots/execution_code_view.png" alt="Code tracking view" width="30%" style="margin-right: 20px;"/>
  <img src="./screenshots/execution_data_comparison.png" alt="Data comparison across executions" width="30%" style="margin-right: 20px;"/>
</p>
<p align="center">
  <em>Visualize run data (left) • Track code versions (middle) • Compare executions (right)</em>
</p>

### Lineage & Provenance

<p align="center">
  <img src="./screenshots/lineage_view.png" alt="Lineage dependencies view" width="30%"/>
  <img src="./screenshots/lineage_code_view_grouped_by_module.png" alt="Code view grouped by module" width="30%" style="margin-right: 20px;"/>
</p>
<p align="center">
  <em>Trace dependencies (left) • Navigate code visually (right)</em>
</p>

### Catalog

<p align="center">
  <img src="./screenshots/catalog_artifact.png" alt="Artifact catalog view" width="30%"/>
  <img src="./screenshots/catalog_transform.png" alt="Transform catalog view" width="30%" style="margin-right: 20px;"/>
</p>
<p align="center">
  <em>Browse artifacts (left) • Discover features and usage (right)</em>
</p>

---

## 🚀 Quick Start

### Prerequisites

- Docker installed and running on your system

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/apache/hamilton

# 2. Navigate to the UI directory
cd hamilton/ui

# 3. Start the application
./run.sh
```

### Initial Setup

1. Open your browser and navigate to **http://localhost:8242**
2. Create an account with your email
3. Create a new project
4. Follow the on-screen instructions to integrate with Apache Hamilton

For a complete setup guide, visit the [documentation](https://hamilton.apache.org/concepts/ui).

---

## 🏗️ Architecture

The Hamilton UI follows a simple, scalable architecture:

![Architecture Diagram](./hamilton-ui-architecture.png)

**Components:**

- **Tracking Server**: Stores execution data in PostgreSQL and binary objects in S3 (or Docker volumes in local mode)
- **Frontend**: React-based web application
- **Authentication**: Configurable authentication with local/unauthenticated mode as default

> **Note**: For custom authentication requirements, please contact the maintainers.

---

## 🛠️ Development

### Project Structure

The project uses a symlink from `backend/hamilton_ui` to `backend/server` to maintain Django's structure while enabling import as `hamilton_ui`.

> ⚠️ *This structure may be refactored in future versions.*

### Building for Development

```bash
cd hamilton/ui

# Build everything from scratch
./dev.sh --build

# Use local code with pulled Docker images
./dev.sh
```

**Important**: Docker requires **at least 9GB of memory** allocated to build the frontend. Increase your Docker memory allocation if you encounter build issues.

### Building for Production

```bash
cd hamilton/ui

# Pull and run production images
./run.sh

# Rebuild production images
./run.sh --build
```

**Before building**: Clean the `backend/dist/` directory to avoid adding unnecessary files to the Docker image.

### Deployment Process

Use the `admin.py` script in the UI directory to deploy:

1. Builds the frontend
2. Copies build artifacts to the `build/` directory
3. Publishes to PyPI as [`sf-hamilton-ui`](https://pypi.org/project/sf-hamilton-ui/)

**Installation**:
```bash
# Install the UI
pip install sf-hamilton[ui]

# Run the UI
hamilton ui

# Install SDK for API communication
pip install sf-hamilton[sdk]
```

---

## 🐳 Docker Management

### Publishing Backend Images

```bash
# Tag the image with version
docker tag local-image:tagname dagworks/ui-backend:VERSION

# Push versioned image
docker push dagworks/ui-backend:VERSION

# Tag as latest
docker tag dagworks/ui-backend:VERSION dagworks/ui-backend:latest

# Push latest
docker push dagworks/ui-backend:latest
```

### Publishing Frontend Images

```bash
# Tag the image with version
docker tag local-image:tagname dagworks/ui-frontend:VERSION

# Push versioned image
docker push dagworks/ui-frontend:VERSION

# Tag as latest
docker tag dagworks/ui-frontend:VERSION dagworks/ui-frontend:latest

# Push latest
docker push dagworks/ui-frontend:latest
```

---

## 📦 Package Information

- **UI Package**: `sf-hamilton-ui` - The web interface
- **SDK Package**: `sf-hamilton[sdk]` - Required for API communication
- **Full Installation**: `sf-hamilton[ui]` - Includes everything needed to run the UI

---

## 📄 License

Licensed under the Apache License, Version 2.0. See the license header for full details.
