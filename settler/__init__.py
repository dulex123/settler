import os
import git
import click
import json
import string
import random
from pathlib import Path
import shutil

from subprocess import STDOUT, check_call



def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def read_config(path):
    click.echo("Loading config")
    with open(path+'/settler.json', 'r') as f_json:
        data = json.load(f_json)
        click.echo("Installing apt packages:")

        # Install apt-get packages
        for package_name in data['apt-get']:
            install_apt(package_name)

        # Copy directories
        copy_directories(path, data)
        copy_files(path, data)

        return data

def copy_files(path, config):
    home_path=str(Path.home())
    files = {}
    for root, dirs, filesx in os.walk(path):  
        for filename in filesx:
            if filename != 'settler.json':
                filename = str(filename)
                files[filename] = os.path.join(home_path, filename)
        break

    if 'files' in config:
        for filename, filepath in config['files'].items():
            if os.path.exists(os.path.join(path, filename)) and filename != '':
                if os.path.isabs(filepath):
                    files[filename] = filepath
                else:
                    files[filename] = os.path.join(home_path, filepath)

    for filename, dst in files.items():
        click.echo("Saving %s as %s" % (filename, dst))
        src = os.path.join(path, filename)
        shutil.copyfile(src, dst)

def copy_directories(path, config):
    home_path = str(Path.home())
    folders = {}
    for f in os.listdir(path):
        if not os.path.isfile(os.path.join(path, f)) and f != '.git':
            folders[f] = os.path.join(home_path, f)
    if 'folders' in config:
        for foldername, folderpath in config['folders'].items():
            if os.path.exists(os.path.join(path, foldername)) and foldername !='':
                if os.path.isabs(folderpath):
                    folders[foldername] = folderpath
                else:
                    folders[foldername] = os.path.join(home_path, folderpath)

    for foldername, dst in folders.items():
        click.echo("Copying %s to %s" % (foldername, dst))
        src = os.path.join(path, foldername)
        copydir(src, dst)
    print("Folders", folders)


def copydir(source, dest, indent = 0):
    """Copy a directory structure overwriting existing files"""
    for root, dirs, files in os.walk(source):
        if not os.path.isdir(root):
            os.makedirs(root)
        for each_file in files:
            rel_path = root.replace(source, '').lstrip(os.sep)
            dest_path = os.path.join(dest, rel_path, each_file)
            shutil.copyfile(os.path.join(root, each_file), dest_path)

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
