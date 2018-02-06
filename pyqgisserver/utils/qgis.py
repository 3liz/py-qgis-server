""" Start qgis application
"""
import os
import sys
import logging


def darwin_setup():
    """ Set up environment variables for OSX
    """
    prefix = os.environ.get('QGIS3_PREFIX','/Applications')
    if not os.path.exists('%s/QGIS.app' % prefix):
        raise FileNotFoundError('%s/QGIS.app' % prefix)
    os.environ['QGIS3_HOME'] = '%s/QGIS.app/Contents/MacOS' % prefix
    os.environ['QGIS3_PLUGINPATH'] =  '%s/QGIS.app/Contents/Resources/python/plugins' % prefix
    # Set up qgis python bindings path
    sys.path.append('%s/QGIS.app/Contents/Resources/python' % prefix)


def setup_qgis_paths():
    """ Init qgis paths 
    """
    if os.uname()[0].lower() == 'darwin':
        darwin_setup()
    qgis_pluginpath = os.environ.get('QGIS3_PLUGINPATH','/usr/share/qgis/python/plugins/')
    sys.path.append(qgis_pluginpath)
   

#XXX Apparently we need to keep a reference instance of the qgis_application object
# And not make this object garbage collected
qgis_application = None


def start_qgis_application(enable_gui=False, enable_processing=False, verbose=False, cleanup=True,
                           logger=None, logprefix='Qgis:'):
    """ Start qgis application

        :param boolean enable_gui: Enable graphical interface, default to False
        :param boolean enable_processing: Enable processing, default to False
        :param boolean verbose: Output qgis settings, default to False
        :param boolean cleanup: Register atexit hook to close qgisapplication on exit().
            Note that prevents qgis to segfault when exiting. Default to True.
    """

    os.environ['QGIS_NO_OVERRIDE_IMPORT']    = '1'
    os.environ['QGIS_DISABLE_MESSAGE_HOOKS'] = '1'

    logger = logger or logging.getLogger()
    setup_qgis_paths()

    from qgis.core import QgsApplication

    if QgsApplication.QGIS_APPLICATION_NAME != "QGIS3":
        raise RuntimeError("You need QGIS3 (found %s)" % QgsApplication.QGIS_APPLICATION_NAME)

    if not enable_gui:
        #  We MUST set the QT_QPA_PLATFORM to prevent
        #  Qt trying to connect to display in containers
        if os.environ.get('DISPLAY') is None:
            logger.info("Setting offscreen mode")
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'

    qgis_prefix = os.environ.get('QGIS3_HOME','/usr')

    global qgis_application

    qgis_application = QgsApplication([], enable_gui )
    qgis_application.setPrefixPath(qgis_prefix, True)
    qgis_application.initQgis()

    if cleanup:
        # Closing QgsApplication on exit will
        # prevent our app to segfault on exit()
        import atexit

        logger.info("%s Installing cleanup hook" % logprefix)
    
        @atexit.register
        def exitQgis():
            global qgis_application
            if qgis_application:
                qgis_application.exitQgis()
                del qgis_application

    if verbose:
        print(qgis_application.showSettings())

    # Install logger hook
    install_logger_hook(logger, logprefix, verbose=verbose)

    logger.info("%s Qgis application initialized......" % logprefix)

    if enable_processing:
        init_processing()
        logger.info("%s QGis processing initialized" % logprefix)

    return qgis_application


def init_processing():
    from processing.core.Processing import Processing
    from qgis.analysis import QgsNativeAlgorithms
    from qgis.core import QgsApplication
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    Processing.initialize()


def install_logger_hook( logger, logprefix, verbose=False ):
    """ Install message log hook
    """
    from qgis.core import QgsApplication, QgsMessageLog
    # Add a hook to qgis  message log 
    def writelogmessage(message, tag, level):
        arg = '{} {}: {}'.format( logprefix, tag, message )
        if level == QgsMessageLog.WARNING:
            logger.warning(arg)
        elif level == QgsMessageLog.CRITICAL:
            logger.error(arg)
        elif verbose:
            # Qgis is somehow very noisy
            # log only if verbose is set
            logger.info(arg)

    messageLog = QgsApplication.messageLog()
    messageLog.messageReceived.connect( writelogmessage )


def init_qgis_server(network_timeout=20000, **kwargs):
    """ Init Qgis server
    """
    start_qgis_application(**kwargs)

    # XXX HACK issue a dummy request for initializing
    # network stuff
    # This is a workaround to https://issues.qgis.org/issues/17866
    from qgis.core import QgsProviderRegistry
    from qgis.PyQt.QtCore import QSettings

    wmsuri = ("contextualWMSLegend=0&crs=EPSG:4326&dpiMode=7&featureCount=10&format=image/jpeg"
      "&layers=s2cloudless&styles&amp;tileMatrixSet=s2cloudless-wmsc-14"
      "&url=http://localhost:8080/?" )
   
    # XXX This will fail with a timeout, subesquent requests should
    # be ok then
    s = QSettings()
    s.setValue('/qgis/networkAndProxy/networkTimeout', 3000)
    provider = QgsProviderRegistry.instance().createProvider( "wms", wmsuri )

    # Set configuration settings
    s.setValue( '/qgis/networkAndProxy/networkTimeout', network_timeout)

    from qgis.server import QgsServer
    return  QgsServer()

