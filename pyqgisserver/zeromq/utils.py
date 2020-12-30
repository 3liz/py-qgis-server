
from ..config import confservice

def _get_ipc( name ) -> str:
    ipc_path = confservice['zmq']['ipcpath']
    return f"ipc://{ipc_path}/{name}"

