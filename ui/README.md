# Apache Hamilton UI

This contains the code for the new Apache Hamilton UI. For an overview of getting started & features
[see this documentation](https://hamilton.apache.org/concepts/ui). For a lengthier post and intro see our [blog post](https://blog.dagworks.io/p/hamilton-ui-streamlining-metadata).

## One operational UI for all your dataflows

The Apache Hamilton UI is a system that provides the following capabilities:

1. Execution tracking with associated metadata
   * Provides a persistent database to store/manage these
   * Provides a server that allows reading/writing/authentication
2. Data/artifact observability: provides telemetry/observability of Apache Hamilton executions + specific function results/code through a web interface
3. Lineage & provenance: allows you to quickly inspect how code and data is connected.
4. Catalog: everything is observed and cataloged, so you can quickly search and find what exists and when it was run.

The UI is meant to monitor/debug Apache Hamilton dataflows both in **development** and **production**. The aim is to enable
dataflow authors to move faster during all phases of the software development lifecycle.

For an overview of some of these features [you can watch this quick video](https://youtu.be/0VIVSeN7Ij8?si=maeV0zdzTPSqUl1N).

### Execution Tracking

<p align="center">
  <img src="./screenshots/execution_waterfall_view.png" alt="Description1" width="30%" style="margin-right: 20px;"/>
  <img src="./screenshots/execution_graph_error.png" alt="Description2" width="30%" style="margin-right: 20px;"/>
  <img src="./screenshots/execution_comparison_waterfall.png" alt="Description3" width="30%"/>
</p>
<p align="center">
  <em>See what's slow (left), pinpoint errors (middle) compare execution performance (right)</em>
</p>

### Data/Artifact Observability

<p align="center">
  <img src="./screenshots/execution_data_view.png" alt="Description3" width="30%"/>
  <img src="./screenshots/execution_code_view.png" alt="Description2" width="30%" style="margin-right: 20px;"/>
  <img src="./screenshots/execution_data_comparison.png" alt="Description1" width="30%" style="margin-right: 20px;"/>
</p>
<p align="center">
  <em>Visualize data for a run (left), track code the run used (middle) compare data across executions (right)</em>
</p>

### Lineage & Provenance

<p align="center">
  <img src="./screenshots/lineage_view.png" alt="Description3" width="30%"/>
  <img src="./screenshots/lineage_code_view_grouped_by_module.png" alt="Description2" width="30%" style="margin-right: 20px;"/>
</p>
<p align="center">
  <em>See how things connect: what's upstream/downstream (left), walk through code visually (right) </em>
</p>

### Catalog

<p align="center">
  <img src="./screenshots/catalog_artifact.png" alt="Description3" width="30%"/>
  <img src="./screenshots/catalog_transform.png" alt="Description2" width="30%" style="margin-right: 20px;"/>
</p>
<p align="center">
  <em>Understand artifacts produced (left), find features and when they were used (right) </em>
</p>

## Getting started

You can watch this [video walkthrough on getting set up](https://youtu.be/DPfxlTwaNsM).

Make sure you have docker running:
```bash
# clone the repository if you haven't
git clone https://github.com/apache/hamilton
# change into the UI directory
cd hamilton/ui
# run docker
./run.sh
```
Once docker is running navigate to http://localhost:8242 and create an email and a project; then follow
instructions on integrating with Apache Hamilton.

A fuller guide can be found [here](https://hamilton.apache.org/concepts/ui).

## Architecture

The architecture is simple.

![architecture-diagram](./hamilton-ui-architecture.png)

The tracking server stores data on postgres, as well as any blobs on s3. This is stored in a docker volume
on local mode. The frontend is a simple React application. There are a few authentication/ACL capabilities,
but the default is to use local/unauthenticated (open). Please talk to us if you have a need for more custom authentication.


## Development

The structure involves a bit of cleverness to ensure the UI can easily be deployed and served from the CLI.

We have a symlink from `backend/hamilton_ui` to `backend/server`, allowing us to work with django's structure
while simultaneously allowing for import as hamilton_ui. (this should probably be changed at some point but not worth it now).

To deploy, use the `admin.py` script in the UI directory.

This:

1. Builds the frontend
2. Copies it into the build/ directory
3. Publishes to the [sf-hamilton-ui](https://pypi.org/project/sf-hamilton-ui/) package on pypi

Then you'll run it with `hamilton ui` after installing `sf-hamilton[ui]`. Note to
talk to it you'll need the hamilton_sdk pacakge which can be installed with `pip install sf-hamilton[sdk]`.


## Building docker
### Dev mode
For development you'll want to run

```bash
cd hamilton/ui
./dev.sh --build # to build it all
./dev.sh # to pull docker images but use local code
```
### You need 9GB assigned to Docker or more to build the frontend
The frontend build requires around 8GB of memory to be assigned to docker to build.
If you run into this, bump your docker memory allocation up to 9GB or more.


### Prod mode
For production build you'll want to run

```bash
cd hamilton/ui
./run.sh # to pull from docker and run
./run.sh --build # to rebuild images for prod

```
#### Caveats:
You'll want to clean the `backend/dist/` directory to not add unnecessary files to the docker image.


### Pushing
How to push to docker hub:
```bash
# retag if needed
docker tag local-image:tagname dagworks/ui-backend:VERSION
# push built image
docker push dagworks/ui-backend:VERSION
# retag as latest
docker tag dagworks/ui-backend:VERSION dagworks/ui-backend:latest
# push latest
docker push dagworks/ui-backend:latest
```

```bash
# retag if needed
docker tag local-image:tagname dagworks/ui-frontend:VERSION
# push built image
docker push dagworks/ui-frontend:VERSION
# retag as latest
docker tag dagworks/ui-backend:VERSION dagworks/ui-backend:latest
# push latest
docker push dagworks/ui-backend:latest
```
