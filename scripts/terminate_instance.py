#!/usr/bin/env python

import argparse
import boto.ec2
import sys

class Terminator(object):
  """
  Hasta la vista, baby
  But seriously, it terminates an ec2 instance
  """

  def __init__(self, *args, **kwargs):
    """
    @param args - not used
    @param kwargs - required arguments: instace_name
                    optional arguments: region, key_name, zone
    """
    # get args
    self._region = kwargs.get('region', 'us-east-1')
    self._zone = kwargs.get('zone', self.default_zone(self._region))
    self._key_name = kwargs.get('key_name', 'watchtower-key')
    self._test_mode = kwargs.get('test', False)
    self._instance_name = kwargs['instance_name']

  def default_zone(self, region):
    """get default zone in given region"""
    if region == 'us-east-1':
      return region + 'b'
    else:
      return region + 'a'

  def terminate_instance(self):
    """
    terminate an ec2 instance
    """
    # connect to ec2
    try:
      ec2_region = [r for r in boto.ec2.regions() if r.name == self._region][0]
    except indexerror:
      print >> sys.stderr, 'unknown region: %s' % self._region
      exit(2)
    ec2_connection = ec2_region.connect()

    #import code; code.interact(local=locals())
    instances = reduce(list.__add__, [reservation.instances for reservation in ec2_connection.get_all_instances()])
    name_matches = [i for i in instances
                    if i.tags.get('Name', None) == self._instance_name and i.state == 'running']

    if (not name_matches):
      raise ValueError('No instance found with name %s' % self._instance_name)
    elif len(name_matches) > 1:
      raise ValueError('Multiple instances found with name %s' % self._instance_name)

    instance = name_matches[0]

    ec2_connection.terminate_instances(instance_ids=[instance.id])


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='add an ec2 instance')
  # note - dashes in arguments mapped to underscores
  parser.add_argument('--instance_name', help='name of instance to terminate', required=True)
  parser.add_argument('--region', help='e.g., us-east-1')
  parser.add_argument('--key-name', help='e.g., watchtower-key')
  parser.add_argument('--instance-name', help='e.g., m1.large')
  parser.add_argument('--zone', help='e.g., us-east-1b')
  parser.add_argument('--test', help="testing mode - don't terminate instance", default=False, action='store_true')

  parser_namespace = parser.parse_args()
  args = dict((k, v) for k, v in vars(parser_namespace).iteritems() if v is not None)  # filter out unspecified args
  terminator = Terminator(**args)
  terminator.terminate_instance()

