# coding=utf-8
"""
Updates hosts file based on docker containers
"""
__author__ = 'talpah@gmail.com'

import json
from os import getenv
import sys
import commands
from lib import Hosts
from docker import Client

HOSTS_PATH = '/host_hosts'
DOMAIN_SUFFIX = '.local.development'


def get_ip(container_id):
    """

    :param container_id:
    :return:
    """
    info = docker.inspect_container(container_id)
    return info['NetworkSettings']['IPAddress']


def get_hostname(container_id):
    """

    :param container_id:
    :return:
    """
    info = docker.inspect_container(container_id)
    dom_name = DOMAIN_SUFFIX
    hostname = container_id
    if info['Config']['Domainname']:
        dom_name = info['Config']['Domainname']
        if dom_name[0] != '.':
            dom_name = '.%s' % dom_name
    if info['Config']['Hostname']:
        hostname = info['Config']['Hostname']
        return "%s%s" % (hostname, dom_name)
    else:
        return None


if __name__ == '__main__':

    docker = Client()
    hostname = getenv('HOSTNAME', None)
    if hostname:
        if '.' not in hostname:
            hostname = "%s%s" % (hostname, DOMAIN_SUFFIX)
        print "Adding %s" % hostname
        hosts = Hosts(HOSTS_PATH)
        my_ip = commands.getoutput("ip -4 -f inet -o addr show eth0 | awk '{print $4}' | cut -d/ -f1")
        hosts.set_one(hostname, my_ip)
        hosts.write(HOSTS_PATH)
        print "Go to http://%s/" % hostname

    for event in docker.events():
        event = json.loads(event)
        if 'status' not in event:
            continue
        if event['status'] == 'start':
            hostname = get_hostname(event['id'])
            if hostname is None:
                continue
            print "Adding %s" % hostname
            hosts = Hosts(HOSTS_PATH)
            hosts.set_one(hostname, get_ip(event['id']))
            hosts.write(HOSTS_PATH)
        elif event['status'] == 'die':
            hostname = get_hostname(event['id'])
            print "Removing %s" % hostname
            hosts = Hosts(HOSTS_PATH)
            hosts.remove_one(hostname)
            hosts.write(HOSTS_PATH)
