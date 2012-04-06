# coding: utf-8

from distutils.core import setup

import _meta

requirements = []

try:
    import configparser
except ImportError:
    requirements.append('configparser')

setup(
    name='sandboxie',
    version=_meta.__version__,
    author='Gregg Gajic',
    author_email='gregg.gajic@gmail.com',
    py_modules=['sandboxie', '_meta'],
    install_requires=requirements,
    classifiers=['Programming Language :: Python',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.2',
                 'Natural Language :: English',
                 'Operating System :: Microsoft :: Windows',
                 'License :: OSI Approved :: MIT License',
                 'Development Status :: 4 - Beta'],
    packages=[],
    scripts=[],
    license=open('LICENSE').read(),
    description='Python interface to Sandboxie.',
    long_description=open('README.rst').read(),
    url='https://github.com/gg/sandboxie-py',
)
