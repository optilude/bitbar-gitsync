#!/usr/bin/env PYTHONIOENCODING=UTF-8 PATH=/usr/local/bin:/usr/bin:/bin python3

# -*- coding: utf-8 -*-
# <bitbar.title>GitSync</bitbar.title>
# <bitbar.version>v0.1</bitbar.version>
# <bitbar.author>Martin Aspeli</bitbar.author>
# <bitbar.author.github>optilude</bitbar.author.github>
# <bitbar.image>https://raw.githubusercontent.com/optilude/bitbar-gitsync/master/screenshot.png</bitbar.image>
# <bitbar.desc>Sync git repositories</bitbar.desc>
# <bitbar.dependencies>python, GitPython</bitbar.dependencies>

import os.path
import configparser
import git

CONFIG_FILE=os.path.expanduser('~/.bitbar-gitsync')

class ConfigError(Exception):
    
    def __init__(self, message):
        self.message = message

class LocalRepo(object):

    def __init__(self, repo, name, pull_from, push_to):
        self.repo = repo
        self.name = name

        self.pull_from = pull_from
        self.push_to = push_to

    @property
    def pull_from(self):
        return self._pull_from

    @pull_from.setter
    def pull_from(self, value):
        if value is not None and value not in [r.name for r in self.repo.remotes]:
            raise ConfigError("Remote %s does not exist for repository %s" % (value, self.name))
        self._pull_from = value
    
    @property
    def push_to(self):
        return self._push_to

    @push_to.setter
    def push_to(self, value):
        if value is not None and value not in [r.name for r in self.repo.remotes]:
            raise ConfigError("Remote %s does not exist for repository %s" % (value, self.name,))
        self._push_to = value

    @staticmethod
    def from_path(path, pull_from=None, push_to=None, context=''):
        if not os.path.isdir(path):
            raise ConfigError("Path %s in %s is not a directory" % (path, context,))
        
        try:
            repo = git.Repo(path)
        except git.exc.NoSuchPathError:
            raise ConfigError("Path %s in %s cannot be read" % (path, context,))
        except git.exc.InvalidGitRepositoryError:
            raise ConfigError("Path %s in %s does not refer to a valid git repository" % (path, context,))
        
        return LocalRepo(
            repo=repo,
            name=os.path.basename(path),
            pull_from=pull_from,
            push_to=push_to,
        )

class Status(object):

    def __init__(self, local_repo, pull=None, push=None):
        self.local_repo = local_repo
        self.pull = pull
        self.push = push

def get_config(filename):
    if not os.path.isfile(filename):
        raise ConfigError("Configuration file %s does not exist" % filename)

    parser = configparser.ConfigParser()
    parser.optionxform = str
    
    parser.read(filename)
    
    paths = {}

    if parser.has_section('pull'):
        for path, remote in parser['pull'].items():
            paths[path] = LocalRepo.from_path(path, pull_from=remote, context="[pull]")
    
    if parser.has_section('push'):
        for path, remote in parser['push'].items():
            if path not in paths:
                paths[path] = LocalRepo.from_path(path, push_to=remote, context="[push]")
            else:
                paths[path].push_to = remote

    return paths.values()

def sync(local_repos):

    statuses = []

    for local_repo in local_repos:
        status = Status(local_repo)
        if local_repo.pull_from is not None:
            
            try:
                fetch_infos = local_repo.repo.remotes[local_repo.pull_from].pull()
            except git.exc.GitCommandError as e:
                status.pull = e.stderr
            else:
                status.pull = True
            
        if local_repo.push_to is not None:
            if status.pull is True or status.pull is None:
                try:
                    push_infos = local_repo.repo.remotes[local_repo.push_to].push()
                except git.exc.GitCommandError as e:
                    status.push = e.stderr
                else:
                    status.push = True
        
        statuses.append(status)
    
    return statuses

def print_menu(error, statuses):

    if error is not None:
        print('❗')
        print('---')
        print(error)
        return

    if any([True for s in statuses if (
        (s.pull is not None and s.pull is not True) or
        (s.push is not None and s.push is not True)
    )]):
        print('❗')
    else:
        print('✔')
    
    print('---')
    
    for status in statuses:
        print("%s: %s%s" % (
            status.local_repo.name,
            '–' if status.pull is None else '⬇' if status.pull is True else '❗',
            '–' if status.push is None else '⬆' if status.push is True else '❗',
        ))

        if status.pull is not None and status.pull is not True:
            print('--%s' % status.pull.replace('\n', '\n--'))
        if status.push is not None and status.push is not True:
            print('--%s' % status.push.replace('\n', '\n--'))

try:

    local_repos = get_config(CONFIG_FILE)

    if len(local_repos) == 0:
        print_menu("No repositories listed to sync found in %s" % CONFIG_FILE, [])

    else:
        statuses = sync(local_repos)
        print_menu(None, statuses)

except ConfigError as e:
    print_menu(e.message, [])
