#!/bin/bash -e

cd $(git rev-parse --show-toplevel)
source bin/activate

# Add instance
cd scripts
#python add_instance.py --instance-type 'm1.large'

#sleep 40

# run on instance
host=`python get_scan_instance.py`
echo "Connecting to host $host..."
ssh -i ~/.ssh/watchtower-key.pem $host "cd ~/watchtower && git pull && source bin/activate && ./scripts/run_cron.sh"

# terminate instance
python terminate_instance.py  --instance_name scan00
