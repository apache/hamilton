#!/bin/bash

. common.sh

# Check if --build parameter is passed
if [[ $1 == "--build" ]]; then
    # Run docker-compose up with project directory, verbose mode and build
    docker-compose --verbose -f docker-compose-prod.yml up --build
else
    # Run docker-compose up with project directory and verbose mode
    docker-compose --verbose -f docker-compose-prod.yml up
fi
