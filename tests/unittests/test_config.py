from pyqgisserver.config import confservice
from pyqgisserver.server import read_configuration


def test_argument_precedence():
    """ Test argument precedences

        From lowest to highest:
         - default
         - environment
         - config file
         - command line
    """
    args = read_configuration([
            '--workers', '3',
            '--port', '9090',
            '--config', 'test.conf',
        ])

    conf = confservice['server']

    # Workers must be 3
    assert args.workers == 3
    assert conf.getint('workers') == 3

    # Port must be 9090
    assert args.port == 9090
    assert conf.getint('port') == 9090

    # rootdir must be '/tmp/' defined in config file
    assert confservice.get('projects.cache', 'rootdir') == '/tmp/'
