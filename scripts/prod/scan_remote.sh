#!/bin/bash

cd $(git rev-parse --show-toplevel)
source bin/activate

# Add instance
cd scripts
python add_instance.py

# TODO run on instance

# TODO terminate instance
