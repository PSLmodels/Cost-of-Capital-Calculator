wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
conda config --set always_yes yes --set changeps1 no
conda update conda
conda create -n test-environment python=$TRAVIS_PYTHON_VERSION pandas numpy
source activate test-environment
conda install --file conda-requirements.txt
export BUILD_DIR=`pwd`
pip install -r requirements.txt
conda install -c ospc taxcalc
pip install coverage codecov pytest-pep8
export BTAX_OUT_DIR=btax_output_dir
export BTAX_CUR_DIR=${BUILD_DIR}
mkdir btax_output_dir
python setup.py develop