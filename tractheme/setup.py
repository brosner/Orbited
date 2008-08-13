#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

from setuptools import setup

setup(
    name = 'orbited_trac_theme',
    version = '1.0',
    packages = ['orbited_trac_theme'],
    package_data = { 'orbited_trac_theme': [
        'templates/*.html',
        'htdocs/*.png',
        'htdocs/*.css'
        ] 
    },

    author = 'Michael Carter',
    author_email = 'CarterMichael@gmail.com',
    description = 'Theme for the Orbited website',
    license = 'MIT',
    keywords = 'trac plugin theme',
    url = 'http://orbited.org',
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['Trac', 'TracThemeEngine>=2.0'],

    entry_points = {
        'trac.plugins': [
            'orbited_trac_theme.theme = orbited_trac_theme.theme',
        ]
    },
)
