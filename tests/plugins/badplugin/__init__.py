from qgis.core import Qgis, QgsMessageLog

def serverClassFactory(serverIface):  # pylint: disable=invalid-name
    """Load wfsOutputExtensionServer class from file wfsOutputExtension.

    :param iface: A QGIS Server interface instance.
    :type iface: QgsServerInterface
    """
    #
    return Foo(serverIface)

class Foo:
    def __init__(self, iface):
        raise RuntimeError("I'am a BAD plugin !")



    
