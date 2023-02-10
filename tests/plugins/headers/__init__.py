from qgis.core import Qgis, QgsMessageLog
from qgis.server import QgsServerFilter

def serverClassFactory(serverIface):  # pylint: disable=invalid-name
    """Load wfsOutputExtensionServer class from file wfsOutputExtension.

    :param iface: A QGIS Server interface instance.
    :type iface: QgsServerInterface
    """
    #
    return Headers(serverIface)

class Headers:
    def __init__(self, iface):
        QgsMessageLog.logMessage("SUCCESS - plugin Headers  initialized")
        self.iface = iface

        iface.registerFilter(HeaderFilter(iface), 10)


class HeaderFilter(QgsServerFilter):
        def __init__(self, iface):
            QgsMessageLog.logMessage("Plugin Initialized", "header_plugin")
            super().__init__(iface)

        def responseComplete(self):
            QgsMessageLog.logMessage("Response Complete", "header_plugin")
            # Check for headers
            handler = self.serverInterface().requestHandler()

            qgis_header = handler.requestHeader('X-Qgis-Test')
            handler.setResponseHeader('X-Qgis-Header',qgis_header)

            lizmap_header = handler.requestHeader('X-Lizmap-Test')
            handler.setResponseHeader('X-Lizmap-Header',lizmap_header)

           


