#from ez_setup import use_setuptools
#use_setuptools()
from setuptools import setup
setup(
    name='pyorbited',
    version='0.1.1',
    author='Michael Carter',
    author_email='CarterMichael@gmail.com',
    url='http://orbited.org',
    download_url='http://orbited.org/download',
    license="MIT License",
    description='A Python client for Orbited (Orbit Event Daemon), a Comet server. Includes three implementations: pyevent, twisted, basic sockets.',
    long_description='',
    packages=["pyorbited"],    
    install_requires = [
#        "event >= 0.3"
    ],
    
#    entry_points = """    
#    [console_scripts]
#    orbited = orbited.start:main
#    """,

    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'],        
    )
    
    
    