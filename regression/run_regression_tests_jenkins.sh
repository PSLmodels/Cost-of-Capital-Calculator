set -x
export MAKE_MINICONDA=1
export REGRESSION_DIR=`pwd`
export TRAVIS_PYTHON_VERSION=2.7
. .run_regression_tests.sh