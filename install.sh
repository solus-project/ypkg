#!/bin/bash
set -x

INST_PREFIX=""
if [[ $EUID -ne "0" ]]; then
    INST_PREFIX="sudo"
fi

if [[ ! -d "$DESTDIR/usr/share/ypkg" ]]; then
    $INST_PREFIX mkdir -vp $DESTDIR/usr/share/ypkg
fi
if [[ ! -d "$DESTDIR/usr/bin" ]]; then
    $INST_PREFIX mkdir -vp $DESTDIR/usr/bin
fi
$INST_PREFIX cp -v */*.py $DESTDIR/usr/share/ypkg/.
$INST_PREFIX chmod -v +x $DESTDIR/usr/share/ypkg/ypkg.py
if [[ ! -e "$DESTDIR/usr/bin/ypkg" ]]; then
    $INST_PREFIX ln -sv /usr/share/ypkg/ypkg.py $DESTDIR/usr/bin/ypkg
fi
