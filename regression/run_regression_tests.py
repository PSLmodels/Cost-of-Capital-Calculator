import argparse
import glob
import json
import os
import pickle
import subprocess as sp

from btax._version import get_versions
from btax.execute import runner

_f = os.path.abspath(__file__)
STANDARDS = os.path.join(os.path.dirname(_f), 'standards')
if not os.path.exists(STANDARDS):
    os.mkdir(STANDARDS)


def get_fname(reform, version):
    return os.path.join(STANDARDS, '{}_{}.pkl'.format(reform, version))


def run_test(reform, start_year, iit_reform, **user_params):
    test_run = bool(int(os.environ.get('BTAX_TEST_RUN') or 0))
    diffs = runner(test_run, start_year, iit_reform, **user_params)
    version = get_versions()['full-revisionid']
    fname = get_fname(reform, version)
    with open(fname, 'wb') as f:
        f.write(pickle.dumps(diffs))
    return diffs


def deltas(reform, diffs):
    all_diffs = {f: pickle.load(open(f, 'rb'))
                 for f in glob.glob(os.path.join(STANDARDS, '*.pkl'))}
    dfs = diffs[:-1]
    js = diffs[-1]
    all_describes = {}
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
                delta[c] = df2[c]
                if not np.all(df2[c].iloc[idx] == df[c].iloc[idx]
                              for idx in range(df.shape[0])
                              if df2[c].iloc[idx] == df2[c].iloc[idx]):
                    print('Fail on ', f, fname)
                    continue
            mn = delta.describe(percentiles=[0.025, 0.05, 0.1, 0.25, 0.5,
                                             0.9, 0.95, 0.75, 0.975])
            all_describes = {}
            all_describes[f] = {'full_delta': delta}
            all_describes[f]['delta_describe'] = mn
            all_describes[f]['diff'] = '{} - {}'.format(f, fname)
    dt = datetime.datetime.utcnow().isoformat()
    all_describes.to_csv(os.path.join(STANDARDS,
                                      'btax_regress_{}.csv').format(dt))
    return all_describes


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

