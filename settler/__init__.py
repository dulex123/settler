import os
import git
import click
import json
import string
import random

from subprocess import STDOUT, check_call



def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def read_config(path):
    click.echo("Loading config")
    with open(path+'/settler.json', 'r') as f_json:
        data = json.load(f_json)
        click.echo("Installing apt packages:")
        for package_name in data['apt-get']:
            install_apt(package_name)
        return data

def install_apt(package_name):
    install_text = click.style('  + %s' % package_name, fg='blue')
    click.echo(install_text)
    check_call(['sudo', 'apt-get', 'install', '-y', package_name],
        stdout=open(os.devnull,'wb'), stderr=STDOUT) 

def clone_repo(backpack, branch):
    text_repo = click.style('%s' % backpack, fg='blue')
    text_branch = click.style('%s' % branch, fg='green')
    click.echo("Cloning " + text_repo + ":" + text_branch)

    # Clone repository
    gh_url = 'https://github.com/' + backpack + '.git'
    local_path = '/tmp/'+random_generator()
    repo = git.Repo.clone_from(gh_url, local_path, branch=branch)

    return local_path

# class Progress(git.remote.RemoteProgress):
    # def update(self, op_code, cur_count, max_count=None, message=''):
        # print(self._cur_line)
