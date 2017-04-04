
if [ "$OSPC_ANACONDA_TOKEN" = "" ];then
    export BTAX_TEST_RUN=1;
else
    export TAXPUF_CHANNEL="https://conda.anaconda.org/t/${OSPC_ANACONDA_TOKEN}/opensourcepolicycenter";
    conda install --force --no-deps -c $TAXPUF_CHANNEL taxpuf;
fi
if [ "$BTAX_REFORMS_FILE" = "" ];then
    export BTAX_REFORMS_FILE="reforms_04_03_2017.json";
fi

rm -f asset_data.pkl


python run_regression_tests.py $BTAX_REFORMS_FILE
