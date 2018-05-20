# BitBar GitSync

A [BitBar](https://getbitbar.com) plugin to periodically sync git repositories.

Requires `gitpython` to be installed:

    $ pip install gitpython

Copy or symlink `gitsync.py` into the BitBar plugins directory with an
appropriate name:

    $ cp `gitsync.py` /path/to/bitbar/plugins/gitsync.10m.py
    $ chmod +x /path/to/bitbar/plugins/gitsync.10m.py

This will run the sync every ten minutes.

Create a config file in `~/.bitbar-gitsync` to list the repositories to sync:

    [pull]
    /path/to/repo1=origin
    /path/to/repo2=another-remote

    [push]
    /path/to/repo1=origin
    /path/to/repo2=another-remote

The format is:

- `[pull]` lists the repositories in which to attempt to pull
- `[push]` lists the repositories in which to attempt to pull
- Each line below `[pull]` or `[push]` is a path to a repository
- The name of the remote to pull from is given after `=` (usually `origin`)

With this configuration, every ten minutes, the two repositories listed will
be pulled, and then pushed. In case of a conflict, the menu bar item will show
a warning.