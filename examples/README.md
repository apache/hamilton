# Examples

Here you'll find various examples, some relatively simple, to a few that are more complex. As you can see
there are MANY examples, that are mostly organized by a thematic topic that matches the folder name they're in.

Note: [hub.dagworks.io](https://hub.dagworks.io/) is also a good spot to find Apache Hamilton examples.

If you have questions, or need help with these examples,
join us on [slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g), and we'll try to help!


## Running examples through a docker image
Examples could also be executed through a docker image which you can build or pull yourself.
Each example directory inside docker image contains a `hamilton-env` Python virtual environment.
`hamilton-env` environment contains all the dependencies required to run the example.

NOTE: If you already have the container image you can skip to container initialization (step 3).

1. Change directory to `examples`.
```bash
cd hamilton/examples
```

2. Build the container image.
```bash
docker build --tag hamilton-example .
```
Docker build takes around `6m16.298s` depending on the system configuration and network.
Alternatively, you can pull the container image from https://hub.docker.com/r/skrawcz/sf-hamilton.
`docker pull skrawcz/sf-hamilton`.

3. Starting the container.
If you built it yourself:
```bash
docker run -it --rm --name hamilton-example hamilton-example
```
If you pulled it from dockerhub:
```bash
docker run -it --rm --name hamilton-example skrawcz/sf-hamilton
```
This will start the container and put you into a bash prompt.

4. Start running examples.
E.g. running the `hello_world` example inside the container:
```bash
cd hamilton/examples/hello_world
source hamilton-env/bin/activate  # this will activate the right python environment
python my_script.py
deactivate # this will deactivate the virtual environment so you can activate another
```
To run another example:
1. change directory to it.
2. activate the environment (`source hamilton-env/bin/activate`).
3. run the code, e.g. `python run.py`.
4. deactivate the environment (`deactivate`).
And then `exit` to quit out of the running docker container.
