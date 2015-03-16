#!/usr/bin/env -e python

import setuptools
from pip.req import parse_requirements

setuptools.setup(
    name='OCCO-Compiler',
    version='0.1.0',
    author='Adam Visegradi',
    author_email='adam.visegradi@sztaki.mta.hu',
    namespace_packages=['occo'],
    packages=['occo.compiler'],
#    scripts=['bin/stowe-towels.py','bin/wash-towels.py'],
    url='http://www.lpds.sztaki.hu/',
    license='LICENSE.txt',
    description='OCCO Infrastructure Compiler Module',
    long_description=open('README.txt').read(),
    install_requires=['PyYAML',
                      'argparse',
                      'dateutils',
                      'OCCO-Util'],
)
