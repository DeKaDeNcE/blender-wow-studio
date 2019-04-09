import subprocess
from distutils.core import run_setup


def build_project():

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

    addon_root_path = os.path.realpath(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/'))

    extension_dirs = (
        "pywowlib/archives/casc/",
        "pywowlib/archives/mpq/native/",
        "pywowlib/blp/BLP2PNG/",
        "pywowlib/blp/PNG2BLP/"

    )

    print('\nBuilding pywowlib C++ extensions.')
    try:
        for module_relpath in extension_dirs:
            os.chdir(os.path.join(addon_root_path, module_relpath))
            run_setup('setup.py', script_args=['build_ext', '--inplace'])

    except PermissionError:
        raise PermissionError("\nThis build script may need to be called with admin (root) rights.")

    os.chdir(addon_root_path)

    print('\nInstalling third-party modules.')

    def install_requirements(f):
        for line in f.readlines():
            status = subprocess.call(['pip3', 'install', line, '-t', 'third_party', '--upgrade'])
            if status:
                print('\nError: failed installing module \"{}\". See pip error above.'.format(line))

    with open('requirements.txt') as f:
        install_requirements(f)

    with open('pywowlib/requirements.txt') as f:
        install_requirements(f)


if __name__ == "__main__":
    build_project()

