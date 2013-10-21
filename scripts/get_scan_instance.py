#!/usr/bin/env python

import boto
import sys

SCAN_SEC_GROUP = 'watchtower-scan'

conn = boto.connect_ec2()

reservations = conn.get_all_instances()
instances = [i for r in reservations for i in r.instances]

for instance in instances:
  for g in instance.groups:
    if g.name == SCAN_SEC_GROUP:
      if instance.public_dns_name != '':
        # fml
        print instance.public_dns_name
