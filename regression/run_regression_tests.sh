
if [ "$OSPC_ANACONDA_TOKEN" = "" ];then
    export BTAX_TEST_RUN=1;
fi


rm -f asset_data.pkl

python run_regression_tests.py
