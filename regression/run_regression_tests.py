from __future__ import print_function, unicode_literals
import argparse
import datetime
import glob
import json
import os
import pickle
import subprocess as sp
from io import BytesIO

import numpy as np
import pandas as pd

from btax._version import get_versions
from btax.execute import runner

_f = os.path.abspath(__file__)
STANDARDS = os.path.join(os.path.dirname(_f), 'standards')
DIFFS = os.path.join(os.path.dirname(_f), 'diffs')
for _f in (DIFFS, STANDARDS):
    if not os.path.exists(_f):
        os.mkdir(_f)


def get_fname(reform, diff_or_standard, version, ending='csv'):
    return os.path.join(diff_or_standard,
                        '{}_{}.{}'.format(reform, version, ending))


def run_test(reform, start_year, iit_reform, **user_params):
    test_run = bool(int(os.environ.get('BTAX_TEST_RUN') or 0))
    diffs = runner(test_run, start_year, iit_reform, **user_params)
    version = get_versions()['full-revisionid']
    fname = get_fname(reform, STANDARDS, version, 'pkl')
    with open(fname, 'wb') as f:
        f.write(pickle.dumps(diffs))
    return diffs


def to_str(c):
    if hasattr(c, 'replace'):
        c = c.replace(u'\xa0', ' ')
    if hasattr(c, 'decode'):
        c = c.decode('utf-8', 'ignore')
    return c


def deltas(reform, diffs):
    all_diffs = {f: pickle.load(open(f))
                 for f in glob.glob(get_fname(reform, STANDARDS, '*', 'pkl'))}
    dfs = diffs[:-1]
    js = diffs[-1]
    for f, df in zip(diffs._fields, dfs):
        for fname, diffs_old in all_diffs.items():
            df2 = getattr(diffs_old, f, None)
            if df2 is None:
                print('Fail on ', f, fname)
                continue
            num_cols, str_cols = [], []
            for c, d in zip(df2.columns, df2.dtypes):
                if 'int' in str(d) or 'float' in str(d):
                    num_cols.append(c)
                else:
                    str_cols.append(c)
            delta = df2[num_cols] - df[num_cols]
            for c in str_cols:
                delta[c] = [to_str(i) for i in df2[c].values]
                if not np.all(df2[c].iloc[idx] == df[c].iloc[idx]
                              for idx in range(df.shape[0])
                              if df2[c].iloc[idx] == df2[c].iloc[idx]):
                    print('Fail on ', f, fname)
                    continue
            desc = delta.describe(percentiles=[0.025, 0.05, 0.1, 0.25, 0.5,
                                               0.75, 0.9, 0.95, 0.975])
            version_pair = '{} - {}'.format(f, os.path.basename(fname))
            dirr = os.path.join(DIFFS, version_pair)
            delta['version_pair'] = desc['version_pair'] = version_pair
            if not os.path.exists(dirr):
                os.mkdir(dirr)
            delta_file = os.path.join(dirr, 'full_delta.csv')
            desc_file  = os.path.join(dirr, 'full_delta_describe.csv')
            delta.columns = [to_str(c) for c in delta.columns]
            delta.index = [to_str(i) for i in delta.index]
            delta.to_csv(delta_file)
            desc.to_csv(desc_file)
    return 0


def run_regression_once(reform, start_year, iit_reform, **user_params):
    diffs = run_test(reform, start_year, iit_reform, **user_params)
    return deltas(reform, diffs)


def run_all_reforms(reforms_file):
    with open(reforms_file) as f:
        reforms = json.load(f)
    for reform, params in reforms.items():
        assert set(params) >= set(('start_year', 'btax_params', 'iit_reform'))
        run_regression_once(reform,
                            params['start_year'],
                            params['iit_reform'],
                            **params['btax_params'])


def cli():
    parser = argparse.ArgumentParser(description='Run B-Tax regression tests')
    parser.add_argument('reforms_file',
                        help='JSON file of reforms')
    return parser.parse_args()


def main():
    args = cli()
    run_all_reforms(args.reforms_file)
    return 0


if __name__ == '__main__':
    main()

