#!/bin/bash

# Recipe and source are stored together
pushd $RECIPE_DIR/..

$PYTHON setup.py install
popd
