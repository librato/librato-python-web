# Copyright (c) 2015. Librato, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Librato, Inc. nor the names of project contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL LIBRATO, INC. BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
from setuptools import setup, find_packages


setup(
    name="librato-python-web",
    version="0.50",
    description=("Librato Python Agent. Copyright (c) 2015 Librato, Inc "
                 "All Rights Reserved"),

    # The project's main homepage
    url="https://github.com/librato/librato-python-web",

    # Author details
    author="Librato, Inc",
    author_email="support@librato.com",

    # Licensing
    license='https://github.com/librato/librato-python-web/blob/master/LICENSE',

    # Classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python'
    ],

    packages=find_packages(exclude=["*.tests", "*.tests.*",
                                    "tests.*", "tests",
                                    "test.*", "test"]),

    install_requires=[
        'six',
        'requests',
        'librato-metrics',
    ],

    dependency_links=[
    ],

    include_package_data=True,

    package_data={
    },

    data_files=[
        ('lib/python{}/dist-packages'.format(sys.version[:3]), ['conf/librato_python_web.pth']),
        ('lib/python{}/site-packages'.format(sys.version[:3]), ['conf/librato_python_web.pth']),
    ],

    scripts=[
    ],

    entry_points={
        'console_scripts': [
            'librato-config=librato_python_web.librato_config:execute',
            'librato-launch=librato_python_web.librato_launch:execute',
            'librato-statsd-server=librato_python_web.librato_statsd_server:execute'],
    }
)
