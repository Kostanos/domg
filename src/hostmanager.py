# coding=utf-8
"""
Updates hosts file based on docker containers
"""
import logging
import sys
from subprocess import check_output

__author__ = 'talpah@gmail.com'

import json
from os import getenv

import docker
from docker.errors import NotFound

from lib import Hosts

HOSTS_PATH = '/host_hosts'
DOMAIN_SUFFIX = '.local.development'

client = docker.from_env()
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def get_ip(container_id):
    """

    :param container_id:
    :return:
    """
    try:
        info = client.api.inspect_container(container_id)
    except docker.errors.NotFound:
        return None
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
    try:
        info = client.api.inspect_container(container_id)
    except docker.errors.NotFound:
        return None
    dom_name = DOMAIN_SUFFIX
    if info['Config']['Domainname']:
        dom_name = info['Config']['Domainname']
        if dom_name[0] != '.':
            dom_name = f".{dom_name}"
    if info['Config']['Hostname']:
        return f"{info['Config']['Hostname']}{dom_name}"
    else:
        return None


if __name__ == '__main__':

    docker = docker.from_env()
    hostname = getenv('HOSTNAME', None)
    if hostname:
        if '.' not in hostname:
            hostname = f"{hostname}{DOMAIN_SUFFIX}"
        logging.info(f"Adding {hostname}")
        hosts = Hosts(HOSTS_PATH)
        my_ip = check_output(["/bin/sh", "-c", "ip -4 -f inet -o addr show eth0 | awk '{print $4}' | cut -d/ -f1"])
        my_ip = my_ip.decode().strip()
        logging.info(f'My IP: {my_ip}')
        hosts.set_one(hostname, my_ip)
        hosts.write(HOSTS_PATH)
        logging.info(f"Go to http://{hostname}/")

    for event in docker.events():
        event = json.loads(event)
        if 'status' not in event:
            continue
        if event['status'] in ['start', 'restart', 'unpause']:
            hostname = get_hostname(event['id'])
            if hostname is None:
                logging.info(f"ERR: Event 'start' received but no hostname found for {event['id']}. Skipping.")
                continue
            container_ip = get_ip(event['id'])
            if not container_ip:
                logging.info(f"ERR: Could not find IP address for {hostname}. Skipping.")
                continue
            logging.info(f"Adding {hostname} as {container_ip}")
            hosts = Hosts(HOSTS_PATH)
            hosts.set_one(hostname, container_ip)
            hosts.write(HOSTS_PATH)
        elif event['status'] in ['die', 'stop', 'pause']:
            hostname = get_hostname(event['id'])
            logging.info(f"Removing {hostname}")
            hosts = Hosts(HOSTS_PATH)
            hosts.remove_one(hostname)
            hosts.write(HOSTS_PATH)
