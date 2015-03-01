#!/bin/bash
set -x

INST_PREFIX=""
if [[ $EUID -ne "0" ]]; then
    INST_PREFIX="sudo"
fi

if [[ ! -d "/usr/share/ypkg" ]]; then
    $INST_PREFIX mkdir -v /usr/share/ypkg
fi
$INST_PREFIX cp -v *.py /usr/share/ypkg/.
$INST_PREFIX chmod -v +x /usr/share/ypkg/ypkg.py
if [[ ! -e "/usr/bin/ypkg" ]]; then
    $INST_PREFIX ln -sv /usr/share/ypkg/ypkg.py /usr/bin/ypkg
fi
