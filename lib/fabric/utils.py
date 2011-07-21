import functools
import getpass
import os
import sys

try:
    from google.appengine.api import appinfo
except ImportError:
    import google
    SDK_PATH = os.path.abspath(
        os.path.dirname(
            os.path.dirname(
                os.path.realpath(google.__file__))))
    EXTRA_PATHS = [
        SDK_PATH,
        os.path.join(SDK_PATH, 'lib', 'antlr3'),
        os.path.join(SDK_PATH, 'lib', 'django'),
        os.path.join(SDK_PATH, 'lib', 'webob'),
        os.path.join(SDK_PATH, 'lib', 'ipaddr'),
        os.path.join(SDK_PATH, 'lib', 'protorpc'),
        os.path.join(SDK_PATH, 'lib', 'yaml', 'lib'),
        os.path.join(SDK_PATH, 'lib', 'fancy_urllib'),
        ]
    sys.path = EXTRA_PATHS + sys.path
    from google.appengine.api import appinfo
finally:
    from google.appengine.ext.remote_api import remote_api_stub
    from google.appengine.tools import dev_appserver, dev_appserver_main

from fabric.api import env


PROJECT_ROOT = os.getcwd()


def with_appcfg(func):
    """Decorator that ensures that the current Fabric env has GAE info
    attached to it at `env.gae`.  Available attributes:

     - env.gae.app_id:  The app's application id (e.g., key-auth)
     - env.gae.version: The app's version
    """
    @functools.wraps(func)
    def decorated_func(*args, **kwargs):
        if not hasattr(env, 'gae'):
            # Load the app.yaml file
            yamlpath = os.path.join(PROJECT_ROOT, 'app.yaml')
            appcfg = appinfo.LoadSingleAppInfo(open(yamlpath))
            # Add the gae object
            env.gae = type('GaeInfo', (), {})
            setattr(env.gae, 'app_id', appcfg.application)
            setattr(env.gae, 'version', appcfg.version)
        return func(*args, **kwargs)
    return decorated_func

@with_appcfg
def deployment_target(version=None):
    """A base modifier for specifying the deployment target.  Knows how to
    adjust the app's version and the gae_host string if a particular version
    is requested."""
    if version:
        env.gae.version = version
        env.gae.host = '%s.latest.%s.appspot.com' % (
            env.gae.version, env.gae.app_id)
    else:
        env.gae.host = '%s.appspot.com' % env.gae.app_id

@with_appcfg
def prep_local_shell():
    """Prepares a local shell by adjusting the datastore paths according to
    the settings and setting up the appropriate stubs."""
    import settings
    args = dev_appserver_main.DEFAULT_ARGS.copy()
    # If a custom datastore directory is requested, modify the args for each
    # of the datastore paths
    if hasattr(settings, 'DATASTORE_DIR'):
        ddir = settings.DATASTORE_DIR
        for key in ('datastore_path', 'history_path', 'blobstore_path'):
            args[key] = os.path.join(ddir, os.path.basename(args[key]))
    # Finally, set up the stubs
    dev_appserver.SetupStubs(env.gae.app_id, **args)

@with_appcfg
def prep_remote_shell(path='/remote_api'):
    """Prepares a remote shell using remote_api located at the given path on
    the given host, if given.  By default, will use the default version of the
    current App Engine application."""
    auth_func = lambda: (raw_input('Email: '), getpass.getpass('Password: '))
    remote_api_stub.ConfigureRemoteApi(
        env.gae.app_id, path, auth_func, servername=env.gae.host)
    remote_api_stub.MaybeInvokeAuthentication()
    os.environ['SERVER_SOFTWARE'] = 'Development (remote_api_shell)/1.0'
