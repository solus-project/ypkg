import os
from setuptools import setup

setup(
    name = "ypkg2",
    version = "7.0.0",
    author = "Ikey Doherty",
    author_email = "ikey@solus-project.com",
    description = ("Solus YPKG build Tool"),
    license = "GPL-3.0",
    keywords = "example documentation tutorial",
    url = "https://github.com/solus-project/ypkg",
    packages=['ypkg2'],
    scripts=['ypkg', 'ypkg-install-deps', 'ypkg-gen-history', 'ypkg-build'],
    classifiers=[
        "License :: OSI Approved :: GPL License",
    ],
)
