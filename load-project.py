import sys
from time import time
from qgis.core import Qgis, QgsProject

import qgis.server
from pyqgisserver.utils import qgis
from pyqgisserver.logger import LOGGER, setup_log_handler

if len(sys.argv) <= 1:
    print("USAGE:", sys.argv[0], "PROJECT")
    sys.exit(1)

setup_log_handler("DEBUG")

app = qgis.start_qgis_application(verbose=True, cleanup=False)
app.initQgis()

uri = sys.argv[1]

LOGGER.debug("Reading Qgis project %s", uri)

# see https://github.com/qgis/QGIS/pull/49266
project = QgsProject(capabilities=Qgis.ProjectCapabilities())
readflags = Qgis.ProjectReadFlags()
readflags |= Qgis.ProjectReadFlag.TrustLayerMetadata
readflags |= Qgis.ProjectReadFlag.ForceReadOnlyLayers
#readflags |= Qgis.ProjectReadFlag.DontLoadLayouts

start = time()

if not project.read(uri):
    raise RuntimeError(f"Failed to read Qgis project {uri}")

elapsed = int((time() - start) * 1000)
print(f"LOAD TIME = {elapsed} ms  [{uri}]")

