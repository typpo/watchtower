#!/bin/bash

cd $(git rev-parse --show-toplevel)
source bin/activate

# Add instance
cd scripts
#python add_instance.py

# run on instance
host=`python get_scan_instance.py`
ssh -i ~/.ssh/watchtower-key.pem $host "./watchtower/scripts/run_cron.sh"

# TODO terminate instance
