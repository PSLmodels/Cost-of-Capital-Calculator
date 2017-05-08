set -x
if [ "$BTAX_VERSIONS" = "" ];then
    export BTAX_VERSIONS="none";
fi

for BTAX_VERSION in "${@}";do
    if [ "$BTAX_VERSION" = "none" ]; then
        echo No install
    else
        . ../.travis_env_setup.sh;
    fi
    #set +x
    if [ "$OSPC_ANACONDA_TOKEN" = "" ];then
        export BTAX_TEST_RUN=1;
    else
        export TAXPUF_CHANNEL="https://conda.anaconda.org/t/${OSPC_ANACONDA_TOKEN}/opensourcepolicycenter";
        conda install --force --no-deps -c $TAXPUF_CHANNEL taxpuf;
    fi
    if [ "$BTAX_REFORMS_FILE" = "" ];then
        export BTAX_REFORMS_FILE="reforms_04_03_2017.json";
    fi
    rm -f asset_data.pkl;
    export dt_str=$(echo $(date) | tr ":" "_" | tr " " "_");
    export output_file="regression_test_out_${dt_str}";
    # Echo the output and write it to file
    conda clean -pt;
    echo Run regression tests on $(date) in PWD:;
    echo `pwd`;
    echo With files: `ls -l`;
    echo Conda "env" list: `conda env list`;
    echo Conda list: `conda list`;
    echo git branch: `git branch`;
    cd $REGRESSION_DIR && python run_regression_tests.py $BTAX_REFORMS_FILE | tee $output_file;
done


