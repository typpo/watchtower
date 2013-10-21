#!/usr/bin/env python

import boto
import time
import sys

SCAN_SEC_GROUP = 'watchtower-scan'

conn = boto.connect_ec2()

while True:
  reservations = conn.get_all_instances()
  instances = [i for r in reservations for i in r.instances]

  for instance in instances:
    for g in instance.groups:
      if g.name == SCAN_SEC_GROUP:
        # fml
        instance.update()
        if instance.public_dns_name != '' and instance.state == 'running':
          print instance.public_dns_name
          sys.exit(0)
  time.sleep(5)
