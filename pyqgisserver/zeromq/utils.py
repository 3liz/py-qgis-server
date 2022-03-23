
from ..config import confservice

def _get_ipc( name: str ) -> str:
    ipc_path = confservice.get('zmq','ipcpath', fallback=None)
    if ipc_path:
        return f"ipc://{ipc_path}/{name}"
    else:
        # Get alternate tcp configuration 
        return confservice.get('zmq', f'{name}_addr')

