#!/bin/bash

pep8 ypkg-build ypkg2/*.py ypkg-gen-history ypkg-install-deps ypkg || exit 1
#for item in examples/*.yml ; do
#    python -m ypkg2.main $item || exit 1
#done

fakeroot ./ypkg-build examples/nano.yml || exit 1
