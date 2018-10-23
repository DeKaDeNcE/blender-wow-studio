try:
    import Cython
except ImportError:
    raise Exception("\nCython is required to build this project")

try:
    from pip import main as pipmain
except ImportError:
    try:
        from pip._internal import main as pipmain
    except ImportError:
        raise Exception("\npip is required to build this project")

import os
import subprocess

ADDON_ROOT_PATH = os.path.realpath(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/'))

cython_module_relpaths = (
    "pywowlib/archives/casc/",
    "pywowlib/blp/"

)

print('\nBuilding pywowlib C++ extensions.')
try:
    for module_relpath in cython_module_relpaths:
        os.chdir(os.path.join(ADDON_ROOT_PATH, module_relpath))
        subprocess.call(["python3", "setup.py", "build_ext", "--inplace"])

except PermissionError:
    raise PermissionError("\nThis build script may need to be called with admin (root) rights.")

os.chdir(ADDON_ROOT_PATH)

print('\nInstalling third-party modules.')

def install_requirements(f):
    for line in f.readlines():
        if 'require-python-3' in line:
            continue

        status = pipmain(['install', line, '-t', 'third_party'])
        if not status:
            print('\nError: failed installing module \"{}\". See pip error above.'.format(line))


with open('requirements.txt') as f:
    install_requirements(f)

with open('pywowlib/requirements.txt') as f:
    install_requirements(f)

