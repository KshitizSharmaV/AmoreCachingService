from distutils.core import setup
import setuptools

setup(
  name = 'ProximityHash',
  py_modules = ['ProximityHash'],
  version = '1.0.1',
  description = 'geohash2es in proximity',
  long_description = open('README.rst').read(),
  author = 'Ashwin Nair',
  author_email = 'ashwinnair.ua@gmail.com',
  license = "MIT",
  url = 'https://github.com/ashwin711/proximityhash',
  download_url = 'https://github.com/ashwin711/proximityhash/tarball/1.0.1',
  keywords = ['geohash', 'optimizer', 'compression', 'geo', 'latitude', 'longitude', 'coordinates', 'proximity', 'circle'],
  classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Apache Software License',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Utilities'
  ],
  install_requires = [
	'clint',
	'argparse',
    'georaptor>=2.0.3',
    'geohash2'
  ],
  entry_points='''
	[console_scripts]
	ProximityHash=ProximityHash:main
  '''
)
