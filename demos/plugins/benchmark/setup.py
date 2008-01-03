#from ez_setup import use_setuptools
#use_setuptools()
from setuptools import setup, find_packages
import os


static_types = [
    '*.js', 
    '*.html',
    '*.css', 
    '*.ico', 
    '*.gif', 
    '*.jpg', 
    '*.png', 
    '*.txt*',
]

setup(
    name='graph',
    version='0.1.0',
    author='Mario Balibrera',
    author_email='MarioBalibrera@gmail.com',
    url='http://www.orbited.org',
    download_url='http://www.orbited.org/download',
    license='MIT License',
    description='An orbited based graph',
    long_description='',
    packages=[
        "graph", 
    ],
    package_data = {
        '': reduce(list.__add__, [ '.svn' not in d and [ os.path.join(d[6:], e) for e in static_types ] or [] for (d, s, f) in os.walk(os.path.join('graph', 'static')) ])
    },
    zip_safe = False,
    install_requires = [
        "orbited >= 0.2",
        # "event >= 0.3"
    ],
    
    entry_points = '''            
        [orbited.plugins]
        graph = graph.main:GraphServer
        
    ''',
    
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],        
)
