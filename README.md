# BitBar GitSync

A [BitBar](https://getbitbar.com) plugin to periodically sync git repositories.

Requires `gitpython` to be installed:

    $ pip install gitpython

Copy or symlink `gitsync.py` into the BitBar plugins directory with an
appropriate name:

    $ cp gitsync.py /path/to/bitbar/plugins/gitsync.10m.py
    $ chmod +x /path/to/bitbar/plugins/gitsync.10m.py

This will run the sync every ten minutes.

Create a config file in `~/.bitbar-gitsync` to list the repositories to sync:

    [My repo]              # name: must be unique
    path = /path/to/repo1  # required: must exist
    remote = origin        # name of remote to pull from/push to (defaults to `origin`)
    pull = all             # what to pull: `none` or `all` (defaults to `all`)
    stage = all            # what to do with unstaged changes (defaults to `none`):
                           #   - `all` means stage all changes, including new files and deletions
                           #   - `tracked` means stage changes to files already tracked
                           #   - `none` means do not stage anything
    push = all             # what to push (defaults to `none`):
                           #   - `all` means commit all staged changes, then push
                           #   - `committed` means push only changes manually committed
                           #   - `none` means do not push at all

With this configuration, every ten minutes, the two repositories listed will
be pulled, all local changes staged and committed, and then pushed. In case of a
problem, the menu bar item will show a warning.

You can add more than one repository to sync. Here's a minimal configuration
that only pulls and never stages, commits, or syncs:

    [Another repo]
    path = ~/another-repo

If you want to pull all changes, and push changes you have staged and committed
yourself, but not automatically stage or commit any changes:

    [Third repo]
    path = ~/third-repo
    pull = all
    push = committed

Or, if you want to stage and commit changes to tracked files, but leave any
new files alone:

    [Fourth repo]
    path = ~/fourth-repo
    pull = all
    stage = tracked
    push = all

You can also make the repository name clickable in the dropdown menu, launching
a command like:

    [Fifth repo]
    path = ~/repo5
    command = /usr/local/bin/github args="/path/to/repo5" terminal=false

This will run the `github` app when you click the item in the BitBar menu with
the argument line `/path/to/repo5`. The use of full paths and quoting improves
the chances that BitBar will actually run the command. Omit `terminal=false` to
launch the binary in a terminal window instead.

The drop-down menu will display a tick mark next to each repository if the
operation(s) completed successfully, or an exclamation mark if there is an
error. In this case, you can see the error by hovering over the name.

If, after running all relevant commands, the repository still has unstaged
changes or untracked files, an asterisk will be shown. Note that this
information is only updated each time the command runs, not in real time!