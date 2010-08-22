from shared import *

if PRODUCTION:
    try:
        from production import *
    except ImportError:
        pass

# Import the above secret settings from a separate (hopefully private) module.
try:
    from secrets import *
except ImportError:
    raise RuntimeError('Could not import secret settings')

# Import any local settings
if not PRODUCTION:
    try:
        from local import *
    except ImportError:
        pass
