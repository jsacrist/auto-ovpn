from .core import *
from .version import get_version


ver = get_version()
__version__ = ver["version"]
__full_revisionid__ = ver["hash"]
del get_version, ver
name = "auto_ovpn"
