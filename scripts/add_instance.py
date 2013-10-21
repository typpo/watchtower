#!/usr/bin/env python

"""
@author Kyle Konrad

Class and driver for launching AWS instances
"""

import argparse
import boto.ec2
import os
import json
import subprocess
import sys
import time
import unicodedata

class Launcher(object):
  # set directories
  BASE_DIR = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).rstrip()
  WORKING_DIR = '/tmp'
  SERVER_TYPE_DELIMITER = '-'
  CONFIG_FILE_NAME = 'config.ip.json'

  def get_next_serial_num(self):
    """
    read server configuration file to figure out next serial number for server
    @param zone        - aws zone with optional staging prefix
    @param server_type - server name describing environment and what services will run on it - not including staging prefix
                         e.g., meta or index-book
    """
    return len([name for name, inst in self.get_instances_by_name().items()
                if name.startswith(self._server_type) and
                inst.state != 'terminated']) 

  def default_zone(self, region):
    """get default zone in given region"""
    if region == 'us-east-1':
      return region + 'b'
    else:
      return region + 'a'

  def get_block_device_map(self):
    """returns the block device mapping for the instance being launched.

    returns:
      boto.ec2.blockdevicemapping: the block device mapping.
    """
    dev_sda1 = boto.ec2.blockdevicemapping.BlockDeviceType()
    dev_sda1.size = self._disk_size  # size in gigabytes.
    bdm = boto.ec2.blockdevicemapping.BlockDeviceMapping()
    bdm['/dev/sda1'] = dev_sda1
    return bdm

  def get_instances(self):
    return reduce(list.__add__,
                  [reservation.instances for reservation in
                   self._connection.get_all_instances()],
                  [])

  def get_instances_by_name(self):
    """
    Returns:
      instances_by_name (dict): {name: instance}

    Assumes names are unique
    """
    return {instance.tags.get('Name', ''):
            instance for instance in self.get_instances()}

  def launch_instance(self):
    """
    launch a new ec2 instance
    """
    # reserve instance
    if self._test_mode:
      print "test mode: not launching"
      instance = None
    else:
      print "launching %s in %s" % (self._server_type, self._zone)
      reservation = self._connection.run_instances(self._ami, key_name=self._key_name,
          instance_type=self._instance_type, security_groups=self._security_groups,
          placement=self._zone, block_device_map=self.get_block_device_map())
      instance = reservation.instances[0]
      while True:  # wait for the instance to come up
        time.sleep(5)
        if instance.update() == 'running':
          break

    # name instance
    print "naming instance",
    full_zone = self._zone
    type_serial_num = self.get_next_serial_num()
    if (type_serial_num > 99):
      raise valueerror("serial num %d is too long" % type_serial_num)
    name = '%s%02d' % (self._server_type, type_serial_num)
    print name
    if not self._test_mode:
      instance.add_tag('Name', name)

  def __init__(self, *args, **kwargs):
    """
    @param args - not used
    @param kwargs - required arguments: None
                    optional arguments: region, server_type, key_name,
                                        instance_type, ami, security_group,
                                        zone
    """
    # get args
    self._region = kwargs.get('region', 'us-east-1')
    self._zone = kwargs.get('zone', self.default_zone(self._region))
    self._key_name = kwargs.get('key_name', 'watchtower-key')
    self._instance_type = kwargs.get('instance_type', 't1.micro')
    self._server_type = kwargs.get('server_type', 'scan')
    self._ami = kwargs.get('ami', 'ami-33b0ed5a')
    self._disk_size = kwargs.get('disk_size', 8)
    self._security_groups = [kwargs.get('security_group', 'watchtower-scan')]
    self._test_mode = kwargs.get('test', False)

    # connect to ec2
    try:
      region = [r for r in boto.ec2.regions() if r.name == self._region][0]
    except indexerror:
      print >> sys.stderr, 'unknown region: %s' % self._region
      exit(2)
    self._connection = region.connect()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='add an ec2 instance')
  # note - dashes in arguments mapped to underscores
  parser.add_argument('--region', help='e.g., us-east-1')
  parser.add_argument('--key-name', help='e.g., watchtower-key')
  parser.add_argument('--instance-type', help='e.g., m1.large')
  parser.add_argument('--server-type', help='e.g., scan')
  parser.add_argument('--ami', help='e.g., ami-d52f63bc')
  parser.add_argument('--disk_size', help='size in GB. e.g., 8')
  parser.add_argument('--security-group', help='e.g., watchtower-scan')
  parser.add_argument('--zone', help='e.g., us-east-1b')
  parser.add_argument('--test', help="testing mode - don't launch instance", default=False, action='store_true')

  parser_namespace = parser.parse_args()
  args = dict((k, v) for k, v in vars(parser_namespace).iteritems() if v is not None)  # filter out unspecified args
  launcher = Launcher(**args)
  launcher.launch_instance()
