
if [ "$MAKE_MINICONDA" = "1" ];then
    cd $HOME
    export mini="$HOME/miniconda";
    rm -rf $mini;
    wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh;
    bash miniconda.sh -b -p $mini;
    export PATH="${mini}/bin:$PATH";
fi
conda config --set always_yes yes --set changeps1 no
conda update conda
conda install conda-build
conda env remove --name test-environment
conda create -n test-environment python=$TRAVIS_PYTHON_VERSION pandas numpy
source activate test-environment

if [ "$BTAX_VERSION" = "" ];then
    echo No checkout
else
    git checkout $BTAX_VERSION
fi
if [ "$TAXCALC_VERSION" = "" ];then
    echo Will conda install latest taxcalc
else
    rm -rf Tax-Calculator;
    git clone http://github.com/open-source-economics/Tax-Calculator;
    if [ "$TAXCALC_INSTALL_METHOD" = "git" ];then
        cd Tax-Calculator && git fetch --all && git fetch origin --tags && git checkout $TAXCALC_VERSION
        conda build conda.recipe --python $TRAVIS_PYTHON_VERSION && conda install --use-local taxcalc
    elif [ "$TAXCALC_VERSION" = "" ];then
        conda install -c ospc taxcalc;
    else
        conda install -c ospc taxcalc=$TAXCALC_VERSION;
    fi
fi
cd $REGRESSION_DIR && conda install --file ../conda-requirements.txt
pip install -r ../requirements.txt
pip install coverage codecov pytest-pep8
export BTAX_OUT_DIR=btax_output_dir
export BTAX_CUR_DIR=$REGRESSION_DIR/..

rm -rf btax_output_dir;mkdir -p btax_output_dir
if [ "$BTAX_INSTALL_METHOD" = "" ];then
    python setup.py develop
else
    conda build ${REGRESSION_DIR}/../conda.recipe --python $TRAVIS_PYTHON_VERSION && conda install --use-local btax
fi

