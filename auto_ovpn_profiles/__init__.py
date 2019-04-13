from .core import *
from ._version import get_versions
__version__ = get_versions()['version']
__full_revisionid__ = get_versions()['full-revisionid']
del get_versions
name = "auto_ovpn_profiles"
