#
# Copyright 2018 3liz
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Start qgis application
"""
import logging
import os
import sys

from typing import Optional

import qgis


def setup_qgis_paths() -> None:
    """ Init qgis paths
    """
    qgis_pluginpath = os.environ.get('QGIS3_PLUGINPATH', '/usr/share/qgis/python/plugins/')
    sys.path.append(qgis_pluginpath)


# XXX Apparently we need to keep a reference instance of the qgis_application object
# And not make this object garbage collected
qgis_application = None


def start_qgis_application(
    enable_processing: bool = False, verbose: bool = False,
    cleanup: bool = True,
    logger: Optional[logging.Logger] = None,
    logprefix: str = 'Qgis:',
) -> qgis.core.QgsApplication:
    """ Start qgis application

        :param boolean enable_processing: Enable processing, default to False
        :param boolean verbose: Output qgis settings, default to False
        :param boolean cleanup: Register atexit hook to close qgisapplication on exit().
            Note that prevents qgis to segfault when exiting. Default to True.
    """
    os.environ['QGIS_NO_OVERRIDE_IMPORT'] = '1'
    os.environ['QGIS_DISABLE_MESSAGE_HOOKS'] = '1'

    logger = logger or logging.getLogger()
    setup_qgis_paths()

    from qgis.core import Qgis, QgsApplication

    logger.info("Starting Qgis application: %s", Qgis.QGIS_VERSION)

    if Qgis.QGIS_VERSION_INT < 32800:
        raise RuntimeError(f"You need QGIS 3.28+ (found {Qgis.QGIS_VERSION_INT})")

    #  We MUST set the QT_QPA_PLATFORM to prevent
    #  Qt trying to connect to display in containers
    display = os.environ.get('DISPLAY')
    if display is None:
        logger.info("Setting offscreen mode")
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    else:
        logger.info(f"Using DISPLAY: {display}")

    qgis_prefix = os.environ.get('QGIS3_HOME', '/usr')

    # XXX Set QGIS_PREFIX_PATH, it seems that setPrefixPath
    # does not do the job correctly
    os.environ['QGIS_PREFIX_PATH'] = qgis_prefix

    global qgis_application

    qgis_application = QgsApplication([], False)
    qgis_application.setPrefixPath(qgis_prefix, True)

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
        print(qgis_application.showSettings())  # noqa T201

    # Install logger hook
    install_logger_hook(logger, logprefix, verbose=verbose)

    logger.info("%s Qgis application initialized......" % logprefix)

    if enable_processing:
        init_processing()
        logger.info("%s QGis processing initialized" % logprefix)

    return qgis_application


def init_processing() -> None:
    from processing.core.Processing import Processing

    from qgis.analysis import QgsNativeAlgorithms
    from qgis.core import QgsApplication
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    Processing.initialize()


def install_logger_hook(logger: logging.Logger, logprefix: str, verbose: bool = False) -> None:
    """ Install message log hook
    """
    from qgis.core import Qgis, QgsApplication

    # Add a hook to qgis  message log

    def writelogmessage(message, tag, level):
        arg = f'{logprefix} {tag}: {message}'
        if level == Qgis.Warning:
            logger.warning(arg)
        elif level == Qgis.Critical:
            logger.error(arg)
        elif verbose:
            # Qgis is somehow very noisy
            # log only if verbose is set
            logger.debug(arg)

    messageLog = QgsApplication.messageLog()
    messageLog.messageReceived.connect(writelogmessage)


def set_proxy_configuration(logger: logging.Logger) -> None:
    """ Display proxy configuration
    """
    from qgis.core import QgsNetworkAccessManager
    from qgis.PyQt.QtNetwork import QNetworkProxy

    nam = QgsNetworkAccessManager.instance()
    nam.setupDefaultProxyAndCache()

    proxy = nam.fallbackProxy()
    proxy_type = proxy.type()
    if proxy_type == QNetworkProxy.NoProxy:
        return

    logger.info(
        "QGIS Proxy configuration enabled: %s:%s, type: %s",
        proxy.hostName(), proxy.port(),
        {
            QNetworkProxy.DefaultProxy: 'DefaultProxy',
            QNetworkProxy.Socks5Proxy: 'Socks5Proxy',
            QNetworkProxy.HttpProxy: 'HttpProxy',
            QNetworkProxy.HttpCachingProxy: 'HttpCachingProxy',
            QNetworkProxy.HttpCachingProxy: 'FtpCachingProxy',
        }.get(proxy_type, 'Undetermined'),
    )


def init_qgis_server(**kwargs) -> qgis.server.QgsServer:
    """ Init Qgis server
    """
    start_qgis_application(**kwargs)

    logger = kwargs.get('logger') or logging.getLogger()

    server = qgis.server.QgsServer()

    # Update the network configuration
    # XXX: At the time the settings are read, the neworkmanager is already
    # initialized, but with the wrong settings
    set_proxy_configuration(logger)

    return server


def print_qgis_version(verbose: bool = False) -> None:
    """ Output the qgis version
    """
    from qgis.core import QgsCommandLineUtils
    print(QgsCommandLineUtils.allVersions())  # noqa T201

    if verbose:
        start_qgis_application(verbose=True)
