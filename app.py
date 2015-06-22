#!/usr/bin/env python
# coding=utf-8

"""
The manager
"""
import json
import os
import re
from time import strptime, mktime

import bottle
from datetime import datetime
from docker import Client
from docker.errors import APIError
from hostmanager import HOSTS_PATH

from lib import FlashMsgPlugin, Hosts, group_containers_by_name, human

STATIC = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')

docker = Client()

app = bottle.default_app()
bottle.SimpleTemplate.defaults = {'app': app}
bottle.TEMPLATE_PATH.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'views'))

PORTS_AND_ICONS = {
    'default': 'glyphicon-minus white',
    '4200': "glyphicon-console",
    '3306': "glyphicon-oil",
    '8080': "glyphicon-globe",
    '80': "glyphicon-globe",
    '443': "glyphicon-globe",
}


def generate_menu():
    items = [
        ('Containers', '/'),
        ('Images', '/images'),
        ('Hosts', '/hosts'),
    ]
    current_route = bottle.request.route
    menu = []
    for item in items:
        label, url = item
        try:
            irt, args = bottle.default_app().match({'PATH_INFO': url, 'REQUEST_METHOD': bottle.request.method})
        except bottle.HTTPError:
            irt = None
        active = ' class="active"' if irt and current_route.name == irt.name else ''
        menu.append('<li%s><a href="%s">%s</a></li>' % (active, url, label))
    return " ".join(menu)


@bottle.route('/', name="index", method="GET")
def index():
    running = docker.containers(quiet=True, all=True)
    container_list = []
    for con in running:
        container_info = docker.inspect_container(con['Id'])
        container_list.append(container_info)

    running_containers = [container for container in container_list if container['State']['Running'] is True]

    human_containers = [container for container in container_list if
                        container['State']['Running'] is False
                        and len(re.findall(r"^[a-f\d]{64}$|^[A-F\d]{64}$", container['Config']['Image'])) == 0]

    computer_containers = [container for container in container_list if
                           container['State']['Running'] is False
                           and len(re.findall(r"^[a-f\d]{64}$|^[A-F\d]{64}$", container['Config']['Image'])) == 1]

    # Sort by name
    running_containers, human_containers, computer_containers = \
        sorted(running_containers, key=lambda x: x['Name']), \
        sorted(human_containers, key=lambda x: x['Name']), \
        sorted(computer_containers, key=lambda x: x['Name'])

    # Then by last used
    running_containers, human_containers, computer_containers = \
        sorted(running_containers, key=lambda x: x['State']['StartedAt'], reverse=True), \
        sorted(human_containers, key=lambda x: x['State']['StartedAt'], reverse=True), \
        sorted(computer_containers, key=lambda x: x['State']['StartedAt'], reverse=True)

    hostname = bottle.request.get_header('Host', 'localhost').split(':')[0]

    running_containers = group_containers_by_name(running_containers)
    human_containers = group_containers_by_name(human_containers)
    computer_containers = group_containers_by_name(computer_containers)

    return bottle.template('index.html',
                           title="DoMG",
                           menu=generate_menu(),
                           hosts=Hosts(HOSTS_PATH).get_reversed(),
                           running_containers=running_containers,
                           human_containers=human_containers,
                           computer_containers=computer_containers,
                           hostname=hostname)


@bottle.route('/details/<container_id>', name="details", method="GET")
def container_details(container_id):
    details = docker.inspect_container(container_id)
    started_at = datetime.fromtimestamp(
        mktime(strptime(details['State']['StartedAt'].split('.')[0], "%Y-%m-%dT%H:%M:%S")))
    raw_finished_at = details['State']['FinishedAt'].split('.')
    if len(raw_finished_at) == 2:
        raw_finished_at = raw_finished_at[0]
    else:
        raw_finished_at = '0001-01-01T00:00:00'
    finished_at = datetime.fromtimestamp(
        mktime(strptime(raw_finished_at, "%Y-%m-%dT%H:%M:%S")))
    details['State']['StartedAt'] = human(started_at, past_tense='{}', future_tense='{}')
    details['State']['FinishedAt'] = human(finished_at)
    details['State']['UpFor'] = human(finished_at - started_at, past_tense='{}', future_tense='{}')
    details['State']['UpFor'] = details['State']['UpFor'] if details['State']['UpFor'] else 'less than a second'
    return bottle.template('details.html',
                           title="DoMG",
                           menu=generate_menu(),
                           details=details)


@bottle.route('/images', name="images", method="GET")
def list_images():
    images = docker.images()
    image_details = [{'tags': img['RepoTags'], 'inspect': docker.inspect_image(img['Id'])} for img in images]
    return bottle.template('images.html', title="Images | DoMG", menu=generate_menu(), images=image_details)


@bottle.route('/deleteimage/<image_id>', name="image_delete", method="GET")
def image_delete(image_id):
    try:
        docker.remove_image(image_id)
        app.flash('Deleted image <em>%s</em>!' % image_id)
    except APIError as e:
        app.flash(e.explanation, 'danger')
    return bottle.redirect(bottle.request.headers.get('Referer', '/images').strip())


@bottle.route('/logs/<container_id>', name="logs", method="GET")
def logs(container_id):
    log = docker.logs(container_id)
    if bottle.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return '<pre>%s</pre>' % log
    return bottle.template('logs.html', title="Logs | DoMG", menu=generate_menu(), log=log)


@bottle.route('/delete/<container_id>', name="delete", method="GET")
def container_delete(container_id):
    try:
        docker.remove_container(container_id)
        app.flash('Deleted container <em>%s</em>!' % container_id)
    except APIError as e:
        app.flash(e.explanation, 'danger')
    return bottle.redirect(bottle.request.headers.get('Referer', '/').strip())


@bottle.route('/stop/<container_id>', name="stop", method="GET")
def container_stop(container_id):
    try:
        docker.stop(container_id)
    except APIError as e:
        bottle.response.content_type = 'application/json'
        return json.dumps({
            'error': e.explanation
        })
    if bottle.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        bottle.response.content_type = 'application/json'
        return json.dumps({
            'href': '/start/%s' % container_id,
            'icon': 'glyphicon-play green'
        })
    return bottle.redirect(bottle.request.headers.get('Referer', '/').strip())


@bottle.route('/start/<container_id>', name="start", method="GET")
def container_start(container_id):
    try:
        docker.start(container_id)
    except APIError as e:
        bottle.response.content_type = 'application/json'
        return json.dumps({
            'error': e.explanation
        })
    if bottle.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        bottle.response.content_type = 'application/json'
        return json.dumps({
            'href': '/stop/%s' % container_id,
            'icon': 'glyphicon-stop red'
        })
    return bottle.redirect(bottle.request.headers.get('Referer', '/').strip())


@bottle.route('/static/<path:path>')
def callback(path):
    return bottle.static_file(path, STATIC)


@bottle.route('/hosts', name="hosts", method="GET")
def list_hosts():
    hosts = Hosts(HOSTS_PATH)
    running_containers = [docker.inspect_container(container['Id']) for container in docker.containers(quiet=True)]
    ip_list = [info['NetworkSettings']['IPAddress'] for info in running_containers if
               'IPAddress' in info['NetworkSettings']]

    return bottle.template('hosts.html',
                           title="Hosts | DoMG",
                           menu=generate_menu(),
                           hosts=hosts,
                           active_ip_list=ip_list,
                           begins_with='172.17.0.')


@bottle.route('/delete-host/<hostname>', name="delete_host", method="GET")
def delete_host(hostname):
    hosts = Hosts(HOSTS_PATH)
    hosts.remove_one(hostname)
    hosts.write(HOSTS_PATH)
    return bottle.redirect(bottle.request.headers.get('Referer', '/').strip())


@bottle.route('/delete-inactive-hosts', name="delete_inactive_hosts", method="GET")
def delete_inactive_hosts():
    running_containers = [docker.inspect_container(container['Id']) for container in docker.containers(quiet=True)]
    active_ip_list = [info['NetworkSettings']['IPAddress'] for info in running_containers if
                      'IPAddress' in info['NetworkSettings']]

    hosts = Hosts(HOSTS_PATH)
    reversed_list = hosts.get_reversed()
    for ip in reversed_list:
        if ip[0:9] == '172.17.0.' and ip not in active_ip_list:
            hosts.remove_all(reversed_list[ip])
    hosts.write(HOSTS_PATH)
    return bottle.redirect(bottle.request.headers.get('Referer', '/').strip())

@bottle.route('/test')
def test():
    hosts_contents = docker.execute('rebagg_mysql_1', 'cat /etc/hosts')
    return hosts_contents


if __name__ == '__main__':
    import socket

    my_ip = socket.gethostbyname(socket.gethostname())
    # print("Go to http://" + my_ip + "/")
    print("Hit Ctrl+C to stop")
    app.install(FlashMsgPlugin(secret='somethingelse'))
    bottle.run(host='0.0.0.0', port=80, quiet=True)
