from google.appengine.tools import dev_appserver, dev_appserver_main
args = dev_appserver_main.DEFAULT_ARGS.copy()
dev_appserver.SetupStubs('pickem', **args)
