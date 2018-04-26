import os
import git
import click
import json
import string
import random
import pickle
from pathlib import Path
import shutil

from subprocess import STDOUT, check_call

import sys


def load_config():
    """
        Load configuration class. If not configured before
        create a new one and save as pickle in homedir/.settler.
    """
    home_dir = os.path.expanduser("~")
    settler_dir = os.path.join(home_dir, ".settler")
    cfg_filepath = os.path.join(settler_dir, "config.pickle")

    # TODO: do this with __new__
    # https://stackoverflow.com/questions/43965376/initialize-object-from-the-pickle-in-the-init-function
    if os.path.isfile(cfg_filepath):
        with open(cfg_filepath, 'rb') as file:
            return pickle.load(file)
    else:
        # click.echo("No settler folder found, initializing new one.", color='green')
        return SettlerConfig()


class SettlerConfig:
    def __init__(self):

        self.home_dir = os.path.expanduser("~")
        settler_dir = os.path.join(self.home_dir, ".settler")
        self.settler_cfg = os.path.join(settler_dir, "config.pickle")

        if not os.path.isdir(settler_dir):
            os.mkdir(settler_dir)

        self.backpacks = {}
        self.backpack_dir = None
        self.backpack_data = None
        self.backpack_name = None

        # self.save_pickle()

    def drop_backpack(self):
        self.backpack_dir = None
        self.backpack_data = None
        self.backpack_name = None

    def load_backpack(self):
        for dir_name in self.backpack_data["folders"]:
            load_dir(dir_name, self.backpack_dir, self.home_dir)

        for filename in self.backpack_data["files"]:
            load_file(filename, self.backpack_dir, self.home_dir)

        #for package_name in self.backpack_data["apt-get"]:
        #    install_apt(package_name)

    def unload_backpack(self):
        for dirname in self.backpack_data["folders"]:
            unload_dir(dirname, self.backpack_dir, self.home_dir)

        for filename in self.backpack_data["files"]:
            unload_file(filename, self.backpack_dir, self.home_dir)

        self.drop_backpack()

    def add_backpack(self, backpack_dir):
        backpack_dir = os.path.abspath(backpack_dir)
        backpack_cfg_path = os.path.join(backpack_dir, "settler.json")
        backpack_data = read_cfg(backpack_cfg_path)

        if self.backpack_dir is None:
            self.backpacks[backpack_data["name"]] = backpack_dir
            self.backpack_data = backpack_data
            self.backpack_dir = backpack_dir
            self.backpack_name = backpack_data["name"]
        else:
            self.backpacks[backpack_data["name"]] = backpack_dir
            click.echo("Backpack " + self.backpack_name + " already loaded", color='red')

    def status(self):
        if self.backpacks:
            rm_list = []
            click.echo("Backpacks:")
            for name, dirpath in sorted(self.backpacks.items()):
                if os.path.isdir(dirpath):
                    if name == self.backpack_name:
                        click.echo(click.style("[x] " + name + " " + dirpath, fg='blue'))
                    else:
                        click.echo("[ ] " + name + " " + dirpath)
                else:
                    click.echo(click.style("Folder not found , removing @ " + dirpath, fg='blue'))
                    rm_list.append(name)

            for key in rm_list:
                self.backpacks.pop(key, None)

    def save_pickle(self):
        with open(self.settler_cfg, "wb") as raw_file:
            pickle.dump(self, raw_file)

    def remove_backpack(self, name):
        if name in self.backpacks:
            self.backpacks.pop(name)
            click.echo(click.style("Removed backpack: " + name, fg='green'))
        else:
            click.echo(click.style("Backpack: " + name + " not registered.", fg='blue'))



def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


def initialize_folder(foldername):
    try:
        os.mkdir("./" + foldername)
        cfg_filepath = os.path.join(foldername, "settler.json")
        with open(cfg_filepath, 'w') as cfg_file:
            default_cfg = """
{
    "name": \""""+foldername+"""\", 
    "apt-get" : [
        "gimp"
    ],
    "folders": [".fakefolder"],
    "files": [".fakerc", ".fakerc2"] 
}"""
            cfg_file.write(default_cfg)
        print(foldername + " created.")
        print("Edit settler.json to add files and folders to settler")
    except OSError:
        print("Folder " + foldername + " already exists.")


def refresh_folder(folderpath):
    cfg_path = os.path.join(folderpath, "settler.json")
    if os.path.isfile(cfg_path):
        print("Check if files need copying")
        cfg_data = read_cfg(folderpath)
    else:
        print("Folder is not a backpack.")


def unload_file(filename, backpack_dir, home_dir):
    src = os.path.join(home_dir, filename)
    dst = os.path.join(backpack_dir, filename)

    if os.path.isfile(dst):
        os.unlink(src)
        shutil.copy(dst, src)
        click.echo(click.style("File: " + dst + " -> " + src, fg='green'))
    else:
        click.echo(click.style("Skipping: File not found @ " + dst, fg='blue'))


def unload_dir(dirname, backpack_dir, home_dir):
    """

    """
    src = os.path.join(home_dir, dirname)
    dst = os.path.join(backpack_dir, dirname)

    if not os.path.isdir(dst):
        click.echo(click.style("Skipping: Folder not found @ " + dst, fg='blue'))
        return

    if os.path.islink(src):
        os.unlink(src)

    if os.path.isdir(src):
        click.echo(click.style("Skipping: Folder already present @ " + src, fg='blue'))
        return

    shutil.copytree(dst, src)
    click.echo(click.style("Dir: " + dst + " -> " + src, fg='green'))


def load_dir(dirname, backpack_dir, home_dir):
    """
        If the dirname has not been loaded it will be:
            1) Moved to the current active backpack
            2) A link pointing to backpack will be placed
    """

    src = os.path.join(home_dir, dirname)
    dst = os.path.join(backpack_dir, dirname)

    if not os.path.isdir(src):
        click.echo(click.style("Skipping: Source directory doesnt exist: @ " + src, fg='blue'))
        return

    if os.path.isdir(dst):
        click.echo(click.style("Skipping: Destination directory already exists @ " + dst, fg='blue'))
        return

    click.echo(click.style("Dir: " + src + " -> " + dst, fg='green'))
    shutil.copytree(src, dst)
    shutil.rmtree(src)
    os.symlink(dst, src)


def load_file(filename, backpack_dir, home_dir):
    """
        If the filename has not been loaded it will be:
            1) Moved to the current active backpack
            2) A link pointing to backpack will be placed
    """

    src = os.path.join(home_dir, filename)
    dst = os.path.join(backpack_dir, filename)
    if os.path.isfile(src):
        # shutil.copy(src, dst)
        # os.remove(src)
        shutil.move(src, dst)
        os.symlink(dst, src)
        click.echo(click.style("File:" + src + " -> " + dst, fg='green'))
    else:
        click.echo(click.style("Skipping: File not found @ " + src, fg='blue'))


def install_apt(package_name):
    install_text = click.style('  + %s' % package_name, fg='blue')
    click.echo(install_text)
    check_call(['sudo', 'apt-get', 'install', '-y', package_name],
               stdout=open(os.devnull, 'wb'), stderr=STDOUT)


def uninstall_apt(package_name):
    pass


def read_cfg(filepath):
    with open(filepath, 'r') as raw_file:
        cfg_data = json.load(raw_file)
        return cfg_data
        #
        # # Install apt-get packages
        # for package_name in cfg_data['apt-get']:
        #     install_apt(package_name)
        #
        # for dirname in cfg_data['folders']:
        #     load_dir(dirname)
        #
        # for filename in cfg_data['files']:
        #     load_file(filename)


def read_config(path):
    click.echo("Loading config")
    with open(path + '/settler.json', 'r') as f_json:
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
    home_path = str(Path.home())
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
            if os.path.exists(os.path.join(path, foldername)) and foldername != '':
                if os.path.isabs(folderpath):
                    folders[foldername] = folderpath
                else:
                    folders[foldername] = os.path.join(home_path, folderpath)

    for foldername, dst in folders.items():
        click.echo("Copying %s to %s" % (foldername, dst))
        src = os.path.join(path, foldername)
        copydir(src, dst)
    print("Folders", folders)


def copydir(source, dest, indent=0):
    """Copy a directory structure overwriting existing files"""
    for root, dirs, files in os.walk(source):
        if not os.path.isdir(root):
            os.makedirs(root)
        for each_file in files:
            rel_path = root.replace(source, '').lstrip(os.sep)
            dest_path = os.path.join(dest, rel_path, each_file)
            shutil.copyfile(os.path.join(root, each_file), dest_path)


def clone_repo(backpack, branch):
    text_repo = click.style('%s' % backpack, fg='blue')
    text_branch = click.style('%s' % branch, fg='green')
    click.echo("Cloning " + text_repo + ":" + text_branch)

    # Clone repository
    gh_url = 'https://github.com/' + backpack + '.git'
    local_path = '/tmp/' + random_generator()
    repo = git.Repo.clone_from(gh_url, local_path, branch=branch)

    return local_path

# class Progress(git.remote.RemoteProgress):
# def update(self, op_code, cur_count, max_count=None, message=''):
# print(self._cur_line)
