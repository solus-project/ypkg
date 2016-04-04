#!/bin/bash

pep8 ypkg2/*.py || exit 1
python -m ypkg2.main examples/nano.yml
