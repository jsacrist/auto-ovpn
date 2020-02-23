from .core import *
from .version import get_version


__version__ = get_version()["version"]
__full_revisionid__ = get_version()["hash"]
del get_version
name = "auto_ovpn_profiles"
