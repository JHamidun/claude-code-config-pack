"""CUDA DLL bootstrap — import this FIRST before sam2/rembg/torch."""
import os
import numpy as np

_site = os.path.dirname(np.__file__).replace('numpy', '')
for _pkg in ['cublas', 'cudnn', 'cuda_runtime', 'cufft', 'curand']:
    _bin = os.path.join(_site, 'nvidia', _pkg, 'bin')
    if os.path.isdir(_bin):
        try:
            os.add_dll_directory(_bin)
        except (AttributeError, OSError):
            pass
        os.environ['PATH'] = _bin + os.pathsep + os.environ.get('PATH', '')
