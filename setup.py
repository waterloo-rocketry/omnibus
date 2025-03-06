from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='omnibus',
    version='1.1.0',
    description='A unified data bus',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/waterloo-rocketry/omnibus',
    author='Waterloo Rocketry',
    author_email='contact@waterloorocketry.com',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',

        'License :: OSI Approved :: MIT License',

        'Operating System :: OS Independent',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows :: Windows 10',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',

        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
    ],
    packages=find_packages(include=['omnibus']),
)
