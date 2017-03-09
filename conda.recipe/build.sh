#!/bin/bash

# Recipe and source are stored together
BLD_DIR=`pwd`
pushd $RECIPE_DIR/..

$PYTHON setup.py install --single-version-externally-managed --record=record.txt

popd