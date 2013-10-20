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

# sys.path.append('..')
# from host_manager import HostManager

class Launcher:
  # set directories
  BASE_DIR = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).rstrip()
  WORKING_DIR = '/tmp'
  SERVER_TYPE_DELIMITER = '-'
  CONFIG_FILE_NAME = 'config.ip.json'

  def update_cluster_config(self):
    """
    call the script that updates the cluster config file
    """
    subprocess.check_call('cp %s/config.ip.json %s/prod_config/config.ip.json' \
                          % (Launcher.WORKING_DIR, Launcher.BASE_DIR), shell=True)

  def canonicalize_server_type(self, server_type):
    """
    put hypen seperated list of server_types in order
    does not handle 'staging-' prefix
    """
    server_types = server_type.split(launcher.server_type_delimiter)
    if 'staging' in server_types:
      raise valueerror('invalid server type: "staging"')
    return launcher.server_type_delimiter.join(server_types)

  def get_next_serial_num(self, zone, server_type):
    """
    read server configuration file to figure out next serial number for server
    @param zone        - aws zone with optional staging prefix
    @param server_type - server name describing environment and what services will run on it - not including staging prefix
                         e.g., meta or index-book
    """
    # get current config
    self.update_cluster_config()
    with open('%s/%s' % (launcher.working_dir, launcher.config_file_name)) as json_file:
      cluster_config = json.load(json_file)  # {zone => {type => ips}}

    # nothing in this zone of this type
    if zone not in cluster_config.keys():
      return 1
    zone_config = cluster_config[zone]  # {type => ips}

    # find machines that are in all server types
    ips = set()
    for s_type in server_type.split(launcher.server_type_delimiter):
      if s_type not in zone_config.keys():
        return 1
      if len(ips) == 0:
        ips = set(zone_config[s_type])
      else:
        ips = ips.intersection(zone_config[s_type])
    return len(ips) + 1

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

  def launch_instance(self):
    """
    launch a new ec2 instance
    """
    # get args
    user = 'watchtower'
    # connect to ec2
    try:
      ec2_region = [r for r in boto.ec2.regions() if r.name == self._region][0]
    except indexerror:
      print >> sys.stderr, 'unknown region: %s' % self._region
      exit(2)
    print boto.config.items('Credentials')
    ec2_connection = ec2_region.connect()

    # reserve instance
    if self._test_mode:
      print "test mode: not launching"
      instance = none
    else:
      print "launching %s in %s" % (self._server_type, self._zone)
      reservation = ec2_connection.run_instances(self._ami, key_name=self._key_name,
          instance_type=self._instance_type, security_groups=self._security_groups,
          placement=self._zone, block_device_map=self.get_block_device_map())
      instance = reservation.instances[0]
      while True:  # wait for the instance to come up
        time.sleep(5)
        if instance.update() == 'running':
          break

    # name instance
    print "naming instance",
    staging_prefix = 'staging-' if self._environment == 'staging' else ''
    full_zone = '%s%s' % (staging_prefix, self._zone)
    type_serial_num = self.get_next_serial_num(full_zone, self._server_type)
    if (type_serial_num > 99):
      raise valueerror("serial num %d is too long" % type_serial_num)
    name = '%s%s%02d' % (staging_prefix, self.canonicalize_server_type(self._server_type), type_serial_num)
    print name
    if not self._test_mode:
      instance.add_tag('name', name)
    # update local dns
    self.update_cluster_config()

    # with the new ip file push
    ip = unicodedata.normalize('nfkd', instance.private_ip_address).encode('ascii', 'ignore')

    # wait until ssh is available
    print "waiting until ssh is avaiable for host"
    #todo(kk)
    #subprocess.check_call(['./scripts/push custom:hn\=%s wait_until_ssh_available' % ip], shell=true)

  def __init__(self, *args, **kwargs):
    """
    @param args - not used
    @param kwargs - required arguments: region, environment, server_type
                    optional arguments: key_name, instance_type, ami, security_group, zone
    """
    # get args
    self._region = kwargs.get('region', 'us-east-1')
    self._zone = kwargs.get('zone', self.default_zone(self._region))
    self._key_name = kwargs.get('key_name', 'watchtower-key')
    self._instance_type = kwargs.get('instance_type', 'm1.large')
    self._server_type = kwargs.get('server_type', 'scan')
    self._ami = kwargs.get('ami', 'ami-33b0ed5a')
    self._disk_size = kwargs.get('disk_size', 8)
    self._security_groups = [kwargs.get('security_group', 'watchtower-scan')]
    self._test_mode = kwargs.get('test', False)

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
  # verify you are running this command from the repo root
  if not Launcher.BASE_DIR == os.getcwd():
    print "Error: must run from root repo root %s" % Launcher.BASE_DIR
    exit(3)
  launcher = Launcher(**args)
  launcher.launch_instance()
