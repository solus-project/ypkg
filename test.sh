#!/bin/bash

pep8 ypkg2/*.py || exit 1
for item in examples/*.yml ; do
    python -m ypkg2.main $item
done
