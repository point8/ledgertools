import os
from setuptools import setup

exec(compile(open('ledgertools/version.py', "rb").read(),
             'ledgertools/version.py',
             'exec'))


setup(
    name='ledgertools',
    description='ledgertools',
    author='Point 8 GmbH',
    author_email='kontakt@point-8.de',
    license='MIT',
    url='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3 :: Only',
    ],
    packages=['ledgertools'],
    version=__version__,
    entry_points={
        'console_scripts': [
            'ledgert = ledgertools.cli:main',
        ]
    },
    package_data={},
    install_requires=['tqdm', 'click'],
)
