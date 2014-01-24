import sys

from .base import *
from .local import *

if "test" in sys.argv:
    from .test import *

if YOUR_POSTGIS_VERSION >= 2:
    POSTGIS_BOX2D = "BOX2D"
else:
    POSTGIS_BOX2D = "ST_BOX2D"
