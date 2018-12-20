""" Read profile data

profiles:
    myprofile:
        # Allowed services
        services:
            - WMS
            - WFS
            ...
        # Override parameters
        parameters:
            MAP: ....
            ....
        # List of  allowed referers:
        allowed_referers:
            - ...
        # List of allowed ips range
        allowed_ips:
            - 192.168.0.3/16
            - ...

    # Other profiles follows

"""
import os
import sys
import logging
import yaml
import traceback

from ipaddress import ip_address, ip_network
from glob import glob 

LOGGER = logging.getLogger('QGSRV')

class Loader(yaml.SafeLoader):

    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)

    def include(self, node):
        """
        """
        fileglob = self.construct_scalar(node)
        if not os.path.isabs(fileglob):
            fileglob = os.path.join(self._root, self.construct_scalar(node))
        value = {}
        for filename in glob(fileglob):
            try:
                with open(filename, 'r') as f:
                    data = yaml.load(f, Loader)
                    if not isinstance(data, dict):
                        raise Exception("Expecting 'dict', not %s" % type(data))
                    value.update(data)
            except Exception as err:
                LOGGER.error("Failed to load %s: %s", filename, err)
                raise

        return value


Loader.add_constructor('!include', Loader.include)


class ProfileError(Exception):
    """ Raised when profil does not match
    """

class _Profile:
    
    def __init__(self, data):
        self._services    = data.get('services')
        self._parameters  = data.get('parameters',{})
        self._allowed_ips = [ip_network(ip) for ip in data.get('allowed_ips',[])]
        self._allowed_referers = data.get('allowed_referers')

    def test_services(self, request):
        """ Test allowed services
        """
        if not self._services:
            return
        service = request.arguments.get('SERVICE')
        if service:
            service = service[-1]
            if isinstance(service,bytes):
                service = service.decode()
            if not service in self._services:
                raise ProfileError("Rejected service %s" % service)

    def test_allowed_referers(self, request):
        """ Test allowed referers
        """
        if self._allowed_referers and request.headers.get('Referer') not in self._allowed_referers:
            raise ProfileError("Rejected referer %s" % request.headers.get('Referer') or 'None')

    def test_allowed_ips(self, request, http_proxy):
        """ Test allowed ips

            If behind a proxy we use the X-Forwarded-For header to check ip
        """
        if len(self._allowed_ips) == 0:
            return

        if http_proxy:
            ip = request.headers.get('X-Forwarded-For')
            if not ip:
                raise ProfileError("Missing or empty 'X-Forwarded-For' header")
        else:
            ip = request.remote_ip
        
        ip = ip_address(ip)
        for ipn in self._allowed_ips:
            if not ip in ipn:
                raise ProfileError("Rejected ip %s" % ip)

    def apply(self, request, http_proxy):
        """ Apply profiles constraints
        """
        request.arguments.update((k,[v.encode()]) for k,v in  self._parameters.items())
        self.test_services(request)
        self.test_allowed_referers(request)
        self.test_allowed_ips(request, http_proxy)
               

class ProfileMngr:
    
    @classmethod
    def initialize( cls, profiles, exit_on_error=True ):
        """ Load profiles data
        """
        try:
            mngr = ProfileMngr()
            mngr.load(profiles)
            return mngr
        except Exception:
            LOGGER.error("Failed to load profiles %s: %s")
            if exit_on_error:
                traceback.print_exc()
                sys.exit(1)
            else:
                raise

    def load( self, profiles):
        LOGGER.info("Reading profiles %s",profiles)
        with open(profiles,'r') as f:
            config = yaml.load(f, Loader=Loader)
        self._profiles = {}
        allow_default = config.get('allow_default_profile', True)
        if allow_default:
            self._profiles['default'] = _Profile(config.get('default',{}))

        self._profiles.update( (k,_Profile(v)) for k,v in config.get('profiles',{}).items() )


    def apply_profile( self, name, request, http_proxy=False):
        """
        """
        try:
            profile = self._profiles.get(name or 'default')
            if profile is None:
                raise ProfileError("Unknown profile")
            profile.apply(request, http_proxy)
            return True
        except ProfileError as err:
            LOGGER.error("Invalid profile '%s': %s", name, err)
        
        return False

