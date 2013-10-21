#!/usr/bin/env python

import boto
import time
import sys

SCAN_SEC_GROUP = 'watchtower-scan'

import socket

def DoesServiceExist(host, port):
  # stackoverflow
  captive_dns_addr = ""
  host_addr = ""

  try:
    captive_dns_addr = socket.gethostbyname("BlahThisDomaynDontExist22.com")
  except:
    pass

  try:
    host_addr = socket.gethostbyname(host)

    if (captive_dns_addr == host_addr):
        return False

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    s.connect((host, port))
    s.close()
  except:
    return False

  return True

conn = boto.connect_ec2()

while True:
  reservations = conn.get_all_instances()
  instances = [i for r in reservations for i in r.instances]

  for instance in instances:
    for g in instance.groups:
      if g.name == SCAN_SEC_GROUP:
        # fml
        status = instance.update()
        if instance.public_dns_name != '' and status == 'running':
          host = instance.public_dns_name
          if DoesServiceExist(host, 22):
            print host
            sys.exit(0)
  time.sleep(5)


