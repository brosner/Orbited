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
    '*.py',
    '*.template'
]

try:
    setup(
        name = 'orbited',
        version = '0.7.10',
        author = 'Michael Carter',
        author_email = 'CarterMichael@gmail.com',
        url = 'http://www.orbited.org',
        download_url = 'http://www.orbited.org/download',
        license = 'MIT License',
        description = 'A browser(javascript)->tcp bridge; Comet is used to emulate TCP connections in the browser; Allows you to connect a web browser directly to an IRC or XMPP server, for instance.',
        long_description = '',
        packages = find_packages(),
        package_data = {'': reduce(list.__add__, [ '.svn' not in d and [ os.path.join(d[len('orbited')+1:], e) for e in
                static_types ] or [] for (d, s, f) in os.walk(os.path.join('orbited', 'static'))
            ]) },
        zip_safe = False,
        install_requires = [ "demjson", "morbid >= 0.8.7.1" ],
        entry_points = '''
            [console_scripts]
            orbited = orbited.start:main
        ''',
        classifiers = [
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules'
        ]
    )
except NameError:
    print "\nerror! Orbited NOT installed!"
    print "There is a known conflict between subversion 1.5 and some old versions of setuptools."
    print 'To install Orbited, first update setuptools with the command "easy_install -U setuptools". This is recommended.'
    print "If you don't want the new version of setuptools, you can svn export the checked-out Orbited directory, and run setup.py from there."
    print "(svn export info: http://svnbook.red-bean.com/en/1.0/re10.html)"
