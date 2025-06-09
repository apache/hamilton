FROM python:3.9.14-slim-buster

RUN apt update -y &&\
    apt install git openjdk-11-jdk -y &&\
    git clone https://github.com/apache/hamilton.git --branch=main &&\
    cd hamilton/examples &&\
    bash make_python_virtualenv.sh

ENTRYPOINT ["/bin/bash"]
