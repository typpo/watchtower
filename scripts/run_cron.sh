#!/bin/bash

pushd `dirname $0`

cd ..
source bin/activate
python core/cron.py

popd
