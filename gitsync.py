#!/usr/bin/env PYTHONIOENCODING=UTF-8 PATH=/usr/local/bin:/usr/bin:/bin python3

# -*- coding: utf-8 -*-
# <bitbar.title>GitSync</bitbar.title>
# <bitbar.version>v0.1</bitbar.version>
# <bitbar.author>Martin Aspeli</bitbar.author>
# <bitbar.author.github>optilude</bitbar.author.github>
# <bitbar.image>https://raw.githubusercontent.com/optilude/bitbar-gitsync/master/screenshot.png</bitbar.image>
# <bitbar.desc>Sync git repositories</bitbar.desc>
# <bitbar.dependencies>python, GitPython</bitbar.dependencies>

import socket
import os.path
import configparser
import git

CONFIG_FILE=os.path.expanduser('~/.bitbar-gitsync')

class PullOptions:
    all = 'all'
    none = 'none'

class StageOptions:
    all = 'all'
    tracked = 'tracked'
    none = 'none'

class PushOptions:
    all = 'all'
    committed = 'committed'
    none = 'none'

class ConfigError(Exception):
    
    def __init__(self, message):
        self.message = message

class Status(object):

    def __init__(self, local_repo, pull=None, stage=None, commit=None, push=None, dirty=None):
        self.local_repo = local_repo
        self.pull = pull
        self.stage = stage
        self.commit = commit
        self.push = push
        self.dirty = dirty

class LocalRepo(object):

    def __init__(self, repo, name, remote='origin', pull=None, stage=None, push=None, command=None):
        self.repo = repo
        self.name = name
        self.remote = remote
        self.pull = pull
        self.stage = stage
        self.push = push
        self.command = command

    @property
    def remote(self):
        return self._remote

    @remote.setter
    def remote(self, value):
        if value is not None and value not in [r.name for r in self.repo.remotes]:
            raise ConfigError("Remote %s does not exist for repository %s" % (value, self.name))
        self._remote = value
    
    @property
    def pull(self):
        return self._pull

    @pull.setter
    def pull(self, value):
        if value is not None and value not in (PullOptions.all, PullOptions.none,):
            raise ConfigError("Pull option %s is not valid for repository %s" % (value, self.name))
        self._pull = PullOptions.none if value is None else value
    
    @property
    def stage(self):
        return self._stage

    @stage.setter
    def stage(self, value):
        if value is not None and value not in (StageOptions.all, StageOptions.tracked, StageOptions.none,):
            raise ConfigError("Stage option %s is not valid for repository %s" % (value, self.name))
        self._stage = StageOptions.none if value is None else value
        
    @property
    def push(self):
        return self._push

    @push.setter
    def push(self, value):
        if value is not None and value not in (PushOptions.all, PushOptions.committed, PushOptions.none,):
            raise ConfigError("Push option %s is not valid for repository %s" % (value, self.name))
        self._push = PushOptions.none if value is None else value

def get_config(filename):
    if not os.path.isfile(filename):
        raise ConfigError("Configuration file %s does not exist" % filename)

    parser = configparser.ConfigParser()
    parser.read(filename)
    
    repos = []

    for section in parser.sections():

        name = section
        path = parser[name].get('path', None)
        remote = parser[name].get('remote', 'origin')
        pull = parser[name].get('pull', None)
        stage = parser[name].get('stage', None)
        push = parser[name].get('push', None)
        command = parser[name].get('command', None)

        if path is None:
            raise ConfigError("Path is required for %s" % (name,))
 
        if not os.path.isdir(path):
            raise ConfigError("Path %s for %s is not a directory" % (path, name,))
        
        try:
            repo = git.Repo(path)
        except git.exc.NoSuchPathError:
            raise ConfigError("Path %s for %s cannot be read" % (path, name,))
        except git.exc.InvalidGitRepositoryError:
            raise ConfigError("Path %s for %s does not refer to a valid git repository" % (path, name,))
        
        repos.append(LocalRepo(
            repo=repo,
            name=name,
            remote=remote,
            pull=pull,
            stage=stage,
            push=push,
            command=command
        ))
    

    return repos

def sync_one(local_repo):
    status = Status(local_repo)
    remote = local_repo.remote
    repo = local_repo.repo

    # Pull if `pull = all`
    if local_repo.pull == PullOptions.all:
        try:
            repo.remotes[remote].pull()
        except git.exc.GitCommandError as e:
            status.pull = e.stderr
            return status
        else:
            status.pull = True
    
    # Stage all tracked files if `stage = tracked`
    if local_repo.stage == StageOptions.tracked:
        try:
            repo.git.add(update=True)
        except git.exc.GitCommandError as e:
            status.stage = e.stderr
            return status
        else:
            status.stage = True
    
    # Stage all local files if `stage = all`
    if local_repo.stage == StageOptions.all:
        try:
            repo.git.add(all=True)
        except git.exc.GitCommandError as e:
            status.stage = e.stderr
            return status
        else:
            status.stage = True

    # Commit changes if `push = all` if we have any staged changes to commit
    if local_repo.push == PushOptions.all and len(repo.index.diff(None)) > 0:
        try:
            repo.index.commit("Automatically synced from %s" % socket.gethostname())
        except git.exc.GitCommandError as e:
            status.commit = e.stderr
            return status
        else:
            status.commit = True

    # Push changes if `push = all` or `push = committed`
    if local_repo.push in (PushOptions.all, PushOptions.committed,):
        try:
            repo.remotes[remote].push()
        except git.exc.GitCommandError as e:
            status.push = e.stderr
            return status
        else:
            status.push = True
    
    # Check for diff
    status.dirty = len(repo.index.diff(None)) > 0 or len(repo.untracked_files) > 0

    return status

def sync(local_repos):

    statuses = []

    for local_repo in local_repos:
        status = sync_one(local_repo)
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

        print("%s %s %s%s" % (
            '❗' if any((
                status.pull is not True,
                status.stage is not True,
                status.commit is not True,
                status.push is not True,
            )) else '✔',
            status.local_repo.name,
            '✳' if status.dirty else '',
            (' | bash=%s' % status.local_repo.command.replace('\\', '\\\\')) if status.local_repo.command else '',
        ))

        if isinstance(status.pull, str):
            print('--%s' % status.pull.strip().replace('\n', '\n--'))
        if isinstance(status.stage, str):
            print('--%s' % status.stage.strip().replace('\n', '\n--'))
        if isinstance(status.commit, str):
            print('--%s' % status.commit.strip().replace('\n', '\n--'))
        if isinstance(status.push, str):
            print('--%s' % status.push.strip().replace('\n', '\n--'))

try:

    local_repos = get_config(CONFIG_FILE)

    if len(local_repos) == 0:
        print_menu("No repositories to sync found in %s" % CONFIG_FILE, [])

    else:
        statuses = sync(local_repos)
        print_menu(None, statuses)

except ConfigError as e:
    print_menu(e.message, [])
