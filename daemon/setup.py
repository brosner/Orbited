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
    name='orbited',
    version='0.3.0',
    author='Michael Carter',
    author_email='CarterMichael@gmail.com',
    url='http://www.orbited.org',
    download_url='http://www.orbited.org/download',
    license='MIT License',
    description='A libevent/pyevent based comet server',
    long_description='',
    packages=[
        "orbited", 
        'orbited.http',
        'orbited.orbit',
        # 'orbited.static',
        'orbited.plugins',
        'orbited.plugins.revolved',
        'orbited.plugins.revolved.replication',
        'orbited.plugins.admin',
        'orbited.plugins.simple',
        'orbited.transports',
    ],
    package_data = {
        '': [os.path.join('static', ext) for ext in static_types],
        
        # 'orbited.plugins.admin': reduce(list.__add__, [
        #     '.svn' not in d and
        #         [os.path.join(d, e) for e in static_types] or
        #         []
        #     for (d, s, f) in os.walk('static')
        # ]),
        
        # 'orbited': static_types,
        # 'orbited.plugins.adminscreen': 
        #     [ os.path.join('static', 'helloworld.txt')],
    },
    zip_safe = False,
    install_requires = [
        # "event >= 0.3"
    ],
    
    entry_points = '''    
        [console_scripts]
        orbited = orbited.start:main
        revolved = orbited.plugins.revolved.start:main
        orbited_daemonized = orbited.start:daemon

        [orbited.plugins]
        revolved = orbited.plugins.revolved.main:RevolvedPlugin
        admin = orbited.plugins.admin.main:AdminPlugin
        simple = orbited.plugins.simple.main:SimplePlugin

        [orbited.transports]
        raw = orbited.transports.raw:RawTransport
        basic = orbited.transports.basic:BasicTransport
        stream = orbited.transports.stream:StreamTransport
        iframe = orbited.transports.iframe:IFrameTransport
        xhr_multipart = orbited.transports.xhr_multipart:XHRMultipartTransport
        xhr_stream = orbited.transports.xhr_stream:XHRStreamTransport
        server_sent_events = orbited.transports.sse:ServerSentEventsTransport
    ''',
        ### move these into the plugins section above to enable them (and
        ### also uncomment in the packages list, above)
        ###
        # simple = orbited.plugins.simple.main:SimplePlugin
        # adminscreen = orbited.plugins.adminscreen.main:AdminScreen
        # admin = orbited.plugins.admin.main:AdminPlugin

    
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
