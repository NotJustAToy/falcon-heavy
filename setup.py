#!/usr/bin/env python
import os
import imp
import setuptools

with open('README.rst', 'rb') as readme_file:
    README = readme_file.read().decode('utf-8')

VERSION = imp.load_source('version', os.path.join('.', 'falcon_heavy', 'version.py'))
VERSION = VERSION.__version__

setuptools.setup(
    name='falcon-heavy',
    version=VERSION,
    description="The framework for building app backends and microservices by "
                "specification-first API design approach based on the OpenAPI Specification 3.",
    long_description=README,
    author='Not Just A Toy Corp.',
    author_email='dev@notjustatoy.com',
    url='https://github.com/NotJustAToy/falcon-heavy',
    packages=setuptools.find_packages(exclude=('tests', 'tests.*')),
    keywords='openapi oas oas3',
    zip_safe=False,
    include_package_data=True,
    license='Apache License 2.0',
    python_requires='>=3.6.0',
    install_requires=[
        'PyYAML>=3.12',
        'strict-rfc3339==0.7',
        'rfc3339==6.0',
        'rfc3987==1.3.7',
        'python-mimeparse>=1.5.2',
        'wrapt==1.10.11',
        'cachetools==3.1.0',
        'mypy>=0.711',
        'mypy-extensions>=0.4.1',
    ],
    extras_require={
        'django': [
            'Django>=2.1.0',
        ],
        'falcon': [
            'falcon>=2.0.0',
        ],
        'flask': [
            'Flask>=1.1.0',
        ],
    },
    tests_require=[
        'pytest>=3.1.1,<4',
        'pytest-cov>=2.3.1',
        'pytest-flake8>=0.8.1',
        'pytest-mypy>=0.4.0',
        'safety',
        'piprot',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications',
        'Topic :: Internet',
    ]
)
