"""
Adapted from Key Ingredient's ki.shared.fabric module.

Deployment Targets
------------------

There are two deployment target modifiers, production and staging, which
adjust the deployments to which the other commands apply. Each takes an
optional version modifier, if it should target a non-default version.

For example, to run the shell command on the default production deployment:

    fab production shell

To run the shell command on a specific version of the staging deployment:

    fab staging:1-908ca6a shell

And to get a local shell, you just leave off the deployment target:

    fab shell
"""

from __future__ import with_statement

import datetime
import logging
import os
import sys

from fabric.api import *

# Our own utils for use in this fabfile
import utils


##############################################################################
# Deployment targets -- These can be used to specify which deployment the
# following commands should apply to.
##############################################################################

@utils.with_appcfg
def staging(version=None):
    """Sets the deployment target to staging, with an optional non-default
    version."""
    version = 'staging' + ('-%s' % version if version else '')
    return utils.deployment_target(version=version)

@utils.with_appcfg
def production(version=None):
    """Sets the deployment target to production, with an optional non-default
    version."""
    return utils.deployment_target(version=version)


##############################################################################
# Fabric commands
##############################################################################

def deploy(git=None, inplace=None):
    """Clones the current project's git HEAD to a temporary directory,
updates its submodules, and deploys from the clone.

Optional arguments:

    :git -- Deploy the project with the current git revision appended to its
    version string (like the old --gitversion switch).

    :inplace -- Deploy the project from its working directory, instead of
    making a clean checkout.

Usage:

    # Deploy whatever version is in app.yaml to staging
    fab staging deploy

    # Deploy a version tagged with the current git revision to production
    fab production deploy:git

    # Deploy straight from the working directory
    fab staging deploy:inplace=1

    # Deploy from the working directory, tagged with git revision
    fab production deploy:git,inplace
    """

    # Make sure we've got a deploy target
    if not hasattr(env, 'gae'):
        abort('A deployment target must be specified.')

    # Are we deploying a version tagged with the git revision? If so, update
    # the app's version string accordingly.
    if git is not None:
        gitversion = local('git rev-parse --short HEAD').strip()
        env.gae.version = '%s-%s' % (env.gae.version, gitversion)

    # Are we making a clean checkout from which to deploy?
    if inplace is None:
        # Where are we checking out a clean copy?
        deploy_src = local('mktemp -d -t %s' % env.gae.app_id).strip()

        # Make the clone, check out and update its submodules, and clean up
        # all the resulting git information (trying to make a clean copy of
        # the source).
        local('git clone . %s' % deploy_src)
        with cd(deploy_src):
            local('git submodule init && git submodule update', capture=False)
            local('find . -name ".git*" | xargs rm -rf')

    # Otherwise, we're just deploying from the current directory, as is, but
    # with the app ID and version controlled by the remote target.
    else:
        deploy_src = '.'

    # Copy in deployed secrets file
    with cd(deploy_src):
        local('scp overloaded.org:pickempickem/secrets.py settings/')

    # Deploy the application using appcfg.py
    cmd = 'appcfg.py -A %s -V %s update %s' % (
        env.gae.app_id, env.gae.version, deploy_src)
    local(cmd, capture=False)

    # Clean up after ourselves if we made a clone of the source code
    if inplace is None:
        assert deploy_src not in ('.', env.cwd)
        local('rm -r %s' % deploy_src)

def shell(cmd=None, path='/remote_api'):
    """Launches an interactive shell for this app. If preceded by a deployment
target (e.g. production or staging), a remote_api shell on the given target is
started. Otherwise, a local shell is started.  Uses enhanced ipython or
bpython shells, if available, falling back on the normal Python shell.

Optional arguments:

    :cmd -- A string of valid Python code to be executed on the shell. The
    shell will exit after the code is executed.

    :path -- The path to the remote_api handler on the deployment
    target. Defaults to '/remote_api'.

Usage:

    # A local shell
    fab shell

    # A remote_api shell on production
    fab production shell

    # Run a command directly on production
    fab production shell:cmd="memcache.flush_all()"
"""

    # Import the modules we want to make available by default
    from google.appengine.api import urlfetch
    from google.appengine.api import memcache
    from google.appengine.ext import deferred
    from google.appengine.ext import db

    # Build a dict usable as locals() from the modules we want to use
    modname = lambda m: m.__name__.rpartition('.')[-1]
    mods = [db, deferred, memcache, sys, urlfetch]
    mods = dict((modname(m), m) for m in mods)

    # The banner for either kind of shell
    banner = 'Python %s\n\nImported modules: %s\n' % (
        sys.version, ', '.join(sorted(mods)))

    # Are we running a remote shell?
    if hasattr(env, 'gae'):
        # Add more info to the banner
        loc = '%s%s' % (env.gae.host, path)
        banner = '\nApp Engine remote_api shell\n%s\n\n%s' % (loc, banner)
        # Actually prepare the remote shell
        utils.prep_remote_shell(path=path)

    # Otherwise, we're starting a local shell
    else:
        utils.prep_local_shell()

    # Define the kinds of shells we're going to try to run
    def ipython_shell():
        import IPython
        shell = IPython.Shell.IPShell(argv=[], user_ns=mods)
        shell.mainloop(banner=banner)

    def bpython_shell():
        from bpython import cli
        cli.main(args=[], banner=banner, locals_=mods)

    def plain_shell():
        sys.ps1 = '>>> '
        sys.ps2 = '... '
        code.interact(banner=banner, locals=mods)

    # If we have a command to run, run it.
    if cmd:
        print 'Running remote command: %s' % cmd
        exec cmd in mods

    # Otherwise, start an interactive shell
    else:
        try:
            ipython_shell()
        except ImportError:
            try:
                bpython_shell()
            except ImportError:
                plain_shell()

def loaddata(path):
    """Load the specified JSON fixtures.  If preceded by a deployment target,
the fixture data will be loaded onto that target.  Otherwise they will be
loaded into the local datastore.

Arguments:

    :path -- The path to the fixture data to load

Usage:

    # Load data locally
    fab loaddata:groups/fixtures/test_groups.json

    # Load data onto staging
    fab staging loaddata:groups/fixtures/test_groups.json
"""
    import fixtures

    # Are we loading the fixtures remotely or locally?
    if hasattr(env, 'gae'):
        utils.prep_remote_shell()
    else:
        utils.prep_local_shell()

    # Actually load the fixtures (tweak the logging so their info shows up)
    logging.getLogger().setLevel(logging.INFO)
    fixtures.load_fixtures(path)

def dumpjson(kinds):
    """Dumps data from the local or remote datastore in JSON format.

Arguments:

    :kinds -- A comma-separated list of kinds to dump, specified as
              `path.to.module.ModelName `
    """
    import fixtures
    if hasattr(env, 'gae'):
        utils.prep_remote_shell()
    else:
        utils.prep_local_shell()
    for kind in kinds.split(','):
        print fixtures.serialize_entities(kind)

def dumpdata(kind=None, batch=None, resume=None):
    """Dump data from a remote deployment using the bulkloader.py tool.

Optional arguments:

    :kind -- Limit the dump to entities of this kind.

    :batch -- Dump the data in batches of this size.

    :resume -- The path to a "*-pgrogress-*.sql3" from which to resume.

Usage:

    # Dump all data from staging
    fab staging dumpdata

    # Dump all profiles from production
    fab production dumpdata:Profile
    fab production dumpdata:kind=Profile

    # Dump all recipes in batches of 10
    fab staging dumpdata:Recipe,10
    fab stating dumpdata:kind=Recipe,batch=10

    # Dump everything in batches of 100
    fab staging dumpdata:batch=100

    # Resume a dump from a progress file
    fab staging dumpdata:Recipe,resume=bulkloader-progress-XXX.sql3
"""
    # Eample command:
    #
    # bulkloader.py --dump --app_id="key-usergen"
    # --url="http://key-usergen.appspot.com/remote_api"
    # --db_filename=bulkloader-progress-20100819.084903.sql3
    # --filename="recipes.sql" --kind="Recipe" --batch_size="25"

    if not hasattr(env, 'gae'):
        abort('dumpdata command requires a remote deployment.')

    basename = kind if kind is not None else 'all-kinds'
    datestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = '%s-%s.sql3' % (basename, datestamp)

    args = [
        '--dump',
        '--url="https://%s/remote_api"' % env.gae.host,
        '--app_id="%s"' % env.gae.app_id,
        '--filename="%s"' % filename,
        ]

    if kind:
        args.append('--kind="%s"' % kind)
    if batch:
        args.append('--batch_size="%s"' % batch)
    if resume:
        if not os.path.exists(resume):
            abort('Resume file not found: %s' % resume)
        args.append('--db_filename="%s"' % resume)

    cmd = 'bulkloader.py %s' % ' '.join(args)
    local(cmd, capture=False)

def memcache(cmd='stats'):
    """Operate on a remote deployment's memcache by getting its stats or
clearing its data.

Optional arguments:

    :cmd -- The action to take. Defaults to 'stats'. Must be one of 'stats' or
    'flush'.

Usage:

    # Get production memcache's stats
    fab production memcache:stats

    # Same thing (gets stats by defualt)
    fab production memcache

    # Clear staging memcache
    fab staging memcache:flush
"""
    # Only valid remotely
    if not hasattr(env, 'gae'):
        abort('memcache commands require a remote deployment.')

    # What kind of commands do we know how to run?
    cmds = {
        'stats': 'print memcache.get_stats()',
        'flush': 'memcache.flush_all()',
        }
    # Aliases
    cmds['clear'] = cmds['flush']

    # Make sure we know what to do with the command
    if not cmd in cmds:
        valid_cmds = ', '.join(cmds)
        abort('Invalid memcache command. Valid commands: %s' % valid_cmds)

    # Run the actual Python code via the shell command
    return shell(cmd=cmds[cmd])

def poextract(conf='babel.conf'):
    """Extract all of the translatable strings from the templates
    and update the PO files that exist in locales.  You need pybabel in
    your path and babel and jinja2 installed into the python that pybabel
    uses.  A working method is to install babel and jinja2 with python 2.6
    and run GAE in 2.5.  The output POT file is ki.pot.

Optional arguments:

    :conf -- The configuration file to use, defaults to 'babel.conf'
    """
    local('pybabel extract -F %s . > ki.pot' % conf, capture=False)
    poupdate()

def poinit(locale):
    """Initialize message catalogs. You need pybabel in
    your path and babel and jinja2 installed into the python that pybabel
    uses.  A working method is to install babel and jinja2 with python 2.6
    and run GAE in 2.5.

Arguments:

    :locale -- Locale for the new localized catalog
    """
    import os
    try:
        os.mkdir('locales')
    except: pass

    local('pybabel init -i ki.pot -d locales -l %s' % (locale))

def poupdate():
    """Update all locales. Run after an extract.
    """

    import os
    for folder in sorted(os.listdir('locales')):
        local('pybabel update -i ki.pot -d locales/ -l %s' % folder)

def pocompile():
    """ Compile all recipe catalogs. """
    local('pybabel compile -d locales/ ')

if __name__ == '__main__':
    shell()
