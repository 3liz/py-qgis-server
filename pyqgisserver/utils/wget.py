
from tornado.httpclient import AsyncHTTPClient
from .logger import log_rrequest

async def wget(url, **kwargs):
    """ Return an async request
    """
    http_client = AsyncHTTPClient()
    response = await http_client.fetch(url, raise_error=False, **kwargs)
    log_rrequest(response)
    links = [{"href": url}]
    if response.code == 599:
        raise HTTPError2(504, reason="Backend Timeout", links=links)  
    elif response.code != 200:
       raise HTTPError2(502, reason="Backend Error", links=links)

    return response


