#!/bin/bash

pushd `dirname $0`

sudo apt-get install python-virtualenv python-pip mongodb-server
cd ..
virtualenv .
source bin/activate
pip install -r requirements.txt

python tests/basic_selenium.py

popd
