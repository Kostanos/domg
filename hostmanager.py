# coding=utf-8
"""
Updates hosts file based on docker containers
"""
from subprocess import check_output

__author__ = 'talpah@gmail.com'

import json
from os import getenv

from docker import Client

from lib import Hosts

HOSTS_PATH = '/host_hosts'
DOMAIN_SUFFIX = '.local.development'


def get_ip(container_id):
    """

    :param container_id:
    :return:
    """
    info = docker.inspect_container(container_id)
    ip = info['NetworkSettings']['IPAddress']
    if not ip:
        for net in info['NetworkSettings']['Networks']:
            if info['NetworkSettings']['Networks'][net]['IPAddress']:
                return info['NetworkSettings']['Networks'][net]['IPAddress']
    return ip


def get_hostname(container_id):
    """

    :param container_id:
    :return:
    """
    info = docker.inspect_container(container_id)
    dom_name = DOMAIN_SUFFIX
    if info['Config']['Domainname']:
        dom_name = info['Config']['Domainname']
        if dom_name[0] != '.':
            dom_name = '.%s' % dom_name
    if info['Config']['Hostname']:
        return "%s%s" % (info['Config']['Hostname'], dom_name)
    else:
        return None


if __name__ == '__main__':

    docker = Client()
    hostname = getenv('HOSTNAME', None)
    if hostname:
        if '.' not in hostname:
            hostname = "{}{}".format(hostname, DOMAIN_SUFFIX)
        print("Adding {}".format(hostname))
        hosts = Hosts(HOSTS_PATH)
        my_ip = check_output(["/bin/sh", "-c", "ip -4 -f inet -o addr show eth0 | awk '{print $4}' | cut -d/ -f1"])
        my_ip = my_ip.decode().strip()
        print("My IP: {}" .format(my_ip))
        hosts.set_one(hostname, my_ip)
        hosts.write(HOSTS_PATH)
        print("Go to http://%s/" % hostname)

    for event in docker.events():
        event = json.loads(event)
        if 'status' not in event:
            continue
        if event['status'] == 'start':
            hostname = get_hostname(event['id'])
            if hostname is None:
                print("ERR: Event 'start' received but no hostname found for {}".format(event['id']))
                continue
            container_ip = get_ip(event['id'])
            if not container_ip:
                print("ERR: Could not find IP address for {}".format(hostname))
                continue
            print("Adding {} as {}".format(hostname, container_ip))
            hosts = Hosts(HOSTS_PATH)
            hosts.set_one(hostname, container_ip)
            hosts.write(HOSTS_PATH)
        elif event['status'] == 'die':
            hostname = get_hostname(event['id'])
            print("Removing {}".format(hostname))
            hosts = Hosts(HOSTS_PATH)
            hosts.remove_one(hostname)
            hosts.write(HOSTS_PATH)
