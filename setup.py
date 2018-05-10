"""Setup for short_answer XBlock."""

import os

from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='short_answer-xblock',
    version='0.2.17',
    description='Short Answer XBlock',
    license='MIT',
    packages=[
        'short_answer',
    ],
    install_requires=[
        'XBlock',
    ],
    entry_points={
        'xblock.v1': [
            'short_answer = short_answer:ShortAnswerXBlock',
        ]
    },
    package_data=package_data("short_answer", ["static", "public"]),
)
