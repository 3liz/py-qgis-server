
import urllib.parse

from datetime import datetime
from typing import Optional, Protocol, Tuple

from qgis.core import QgsProject


class ProtocolHandler(Protocol):
    """ Protocol for Handle file protocol
    """

    def get_modified_time(self, url: urllib.parse.ParseResult) -> datetime:
        """ Return the modified date time of the project referenced by its url
        """
        ...

    def get_project(
        self,
        url: Optional[urllib.parse.ParseResult],
        project: Optional[QgsProject] = None,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[QgsProject, datetime]:
        """ Create or return a proect
        """
        ...
