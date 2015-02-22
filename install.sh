#!/bin/bash

if [[ ! -d "/usr/share/ypkg" ]]; then
    sudo mkdir -v /usr/share/ypkg
fi
sudo cp -v *.py /usr/share/ypkg/.
sudo chmod -v +x /usr/share/ypkg/ypkg.py
if [[ ! -e "/usr/bin/ypkg" ]]; then
    sudo ln -sv /usr/share/ypkg/ypkg.py /usr/bin/ypkg
fi
