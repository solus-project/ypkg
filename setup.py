import os
from setuptools import setup

setup(
    name = "ypkg2",
    version = "25.0.0",
    author = "Ikey Doherty",
    author_email = "ikey@solus-project.com",
    description = ("Solus YPKG build Tool"),
    license = "GPL-3.0",
    keywords = "example documentation tutorial",
    url = "https://github.com/solus-project/ypkg",
    packages=['ypkg2'],
    scripts=['ypkg', 'ypkg-install-deps', 'ypkg-gen-history', 'ypkg-build', 'ybump', 'yupdate'],
    classifiers=[
        "License :: OSI Approved :: GPL-3.0 License",
    ],
    package_data={'ypkg2': ['rc.yml']},
    data_files      = [("/usr/share/man/man1", ["man/ypkg.1", "man/ypkg-build.1", "man/ypkg-install-deps.1"]),
                       ("/usr/share/man/man5", ["man/package.yml.5"])]
)
