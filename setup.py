from setuptools import setup, find_namespace_packages
import os

def parse_requirements( filename ):
    with open( filename ) as fp:
        return list(filter(None, (r.strip('\n ').partition('#')[0] for r in fp.readlines())))

def get_version():
    with open('VERSION') as fp:
        return fp.read().strip()

VERSION = get_version()
DESCRIPTION = ('Py-Qgis-Server is an implementation of the OWS standards '
               'standard from the Open Geospatial Consortium.'
               'Py-Qgis-Server written in Python and built on top of Qgis server'
               'implementation')
KEYWORDS = 'QGIS OWS OGC'
kwargs = {}

with open('README.md') as f:
    kwargs['long_description'] = f.read()

# Parse requirement file and transform it to setuptools requirements'''
requirements = 'requirements.txt'
if os.path.exists(requirements):
    kwargs['install_requires']=parse_requirements(requirements)

setup(
    name='py-qgis-server',
    version=VERSION,
    author='3Liz',
    author_email='david.marteau@3liz.com',
    maintainer='David Marteau',
    maintainer_email='dmarteau@3liz.com',
    long_description_content_type="text/markdown",
    description=DESCRIPTION,
    keywords=KEYWORDS,
    url='https://github.com/3liz/py-qgis-server',
    packages=find_namespace_packages(include=['pyqgisserver','pyqgisserver.*',
                                              'pyqgisservercontrib.*']),
    entry_points={
        'console_scripts': [
            'qgisserver = pyqgisserver.server:main',
            'qgisserver-worker = pyqgisserver.qgsworker:main',
        ],
    },
    # Add manifest to main package
    include_package_data=True,
    package_data={"pyqgisserver": ['build.manifest'] },
    python_requires='>=3.6',
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    **kwargs
)
