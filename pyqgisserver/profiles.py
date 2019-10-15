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
import functools

from tornado.web import HTTPError

from yaml.nodes import SequenceNode

from typing import Mapping, TypeVar, Any

from ipaddress import ip_address, ip_network
from glob import glob 

from .watchfiles import watchfiles

LOGGER = logging.getLogger('SRVLOG')

# Define an abstract type for HTTPRequest
HTTPRequest = TypeVar('HTTPRequest')


class Loader(yaml.SafeLoader):
    """ See https://pyyaml.org/wiki/PyYAMLDocumentation
    """  

    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(Loader, self).__init__(stream)

    def include(self, node):
        """
        """
        if isinstance(node, SequenceNode):
            filelist = self.construct_sequence(node)
        else:
            filelist = [ self.construct_scalar(node) ]
        value = {}
        for fileglob in filelist:
            if not os.path.isabs(fileglob):
                fileglob = os.path.join(self._root, fileglob)
            for filename in glob(fileglob):
                try:
                    with open(filename, 'r') as f:
                        data = yaml.load(f, Loader)
                        if not isinstance(data, dict):
                            raise Exception("Expecting 'dict', not %s" % type(data))
                        value.update(data)
                        LOGGER.debug("Loaded profile: %s", filename)
                except Exception as err:
                    LOGGER.error("Failed to load %s: %s", filename, err)
                    raise

        return value


Loader.add_constructor('!include', Loader.include)


class ProfileError(Exception):
    """ Raised when profil does not match
    """

class _Profile:
    
    def __init__(self, data: Mapping[str,Any]) -> None:
        self._services    = data.get('services')
        self._parameters  = data.get('parameters',{})
        self._allowed_ips = [ip_network(ip) for ip in data.get('allowed_ips',[])]
        self._allowed_referers = data.get('allowed_referers')

    def test_services(self, request: HTTPRequest) -> None:
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

    def test_allowed_referers(self, request: HTTPRequest) -> None:
        """ Test allowed referers
        """
        if self._allowed_referers and request.headers.get('Referer') not in self._allowed_referers:
            raise ProfileError("Rejected referer %s" % request.headers.get('Referer') or 'None')

    def test_allowed_ips(self, request: HTTPRequest, http_proxy: bool) -> None:
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

    def apply(self, request: HTTPRequest, http_proxy: bool) -> None:
        """ Apply profiles constraints
        """
        request.arguments.update((k,[v.encode()]) for k,v in  self._parameters.items())
        self.test_services(request)
        self.test_allowed_referers(request)
        self.test_allowed_ips(request, http_proxy)
               

class ProfileMngr:
    
    @classmethod
    def initialize( cls, profiles: str, exit_on_error: bool=True ) -> 'ProfileMngr':
        """ Create Profile manager

            param Profiles: path to profile configuration
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

    def __init__(self) -> None:
        self._autoreload = None

    def load( self, profiles: str) -> None:
        """ Load profile configuration
        """
        LOGGER.info("Reading profiles %s",profiles)
        with open(profiles,'r') as f:
            config = yaml.load(f, Loader=Loader)
        self._profiles = {}
        allow_default = config.get('allow_default_profile', True)
        if allow_default:
            self._profiles['default'] = _Profile(config.get('default',{}))

        self._profiles.update( (k,_Profile(v)) for k,v in config.get('profiles',{}).items() )

        # Configure auto reload
        if config.get('autoreload', False):
            if self._autoreload is None:
                check_time = config.get('autoreload_check_time', 3000)
                self._autoreload = watchfiles([profiles], 
                        lambda modified_files: self.load(profiles), 
                        check_time=check_time)
            if not self._autoreload.is_running():
                LOGGER.info("Enabling profiles autoreload")
                self._autoreload.start()
        elif self._autoreload is not None and self._autoreload.is_running():
            LOGGER.info("Disabling profiles autoreload")
            self._autoreload.stop()            

    def apply_profile( self, name: str, request: HTTPRequest, http_proxy: bool=False) -> bool:
        """ Check profile condition
        """
        try:
            # name may be a path like string
            if name: name = name.strip('/')
            profile = self._profiles.get(name or 'default')
            if profile is None:
                raise ProfileError("Unknown profile")
            profile.apply(request, http_proxy)
            return True
        except ProfileError as err:
            LOGGER.error("Invalid profile '%s': %s", name or "<default>", err)
                
        return False


def register_filters() -> None:
    """
    """
    from pyqgisserver.filters import blockingfilter
    from pyqgisserver.config import get_config, get_env_config

    with_profiles = get_env_config('server','profiles','QGSRV_SERVER_PROFILES')
    if with_profiles:
        mngr = ProfileMngr.initialize(with_profiles)
       
        http_proxy = get_config('server').getboolean('http_proxy')

        @blockingfilter(pri=-1000, uri=r"p/(?P<profile>.*)")
        def profile_filter( handler ):
            # Remove profile from argument list
            profile = handler.path_kwargs.pop('profile')
            if not mngr.apply_profile(profile, handler.request, http_proxy):
                raise HTTPError(403,reason="Unauthorized profile")

        return [profile_filter]
    
    return []

