#!/usr/bin/env python
"""
LeBLEU - Letter-edit / Levenshtein BLEU
"""
import logging


#__all__ = []

__version__ = '0.0.1'
__author__ = 'Stig-Arne Gronroos'
__author_email__ = "stig-arne.gronroos@aalto.fi"

_logger = logging.getLogger(__name__)


def get_version():
    return __version__

# The public api imports need to be at the end of the file,
# so that the package global names are available to the modules
# when they are imported.

from .lebleu import LeBLEU
