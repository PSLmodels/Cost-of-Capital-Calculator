export MAKE_MINICONDA=
export REGRESSION_DIR=`pwd`
if [ "$TRAVIS_PYTHON_VERSION" = "" ];then
    export TRAVIS_PYTHON_VERSION=2.7
fi
. .run_regression_tests.sh