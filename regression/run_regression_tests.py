import os
import pickle
import subprocess as sp

from btax._version import get_versions
from btax.execute import runner

STANDARDS = os.path.join(os.path.abspath(__file__), 'standards')
if not os.path.exists(STANDARDS):
    os.mkdir(STANDARDS)


def get_fname(version):
    return os.path.join(STANDARDS, '{}.pkl'.format(version))


def run_test(start_year, iit_reform, **user_params):
    test_run = bool(int(os.environ.get('BTAX_TEST_RUN') or 0))
    diffs = runner(test_run, start_year, iit_reform, **user_params)
    version = get_versions()['full']
    fname = get_fname(version)
    with open(fname, 'wb') as f:
        f.write(pickle.dumps(diffs))
    return diffs


def deltas(diffs):
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
            delta = df2 - df
            mn = delta.describe(percentiles=[0.025, 0.05, 0.1, 0.25, 0.5,
                                             0.9, 0.95, 0.75, 0.975])
            all_describes[f] = df2 - df
            all_describes[f]['diff'] = '{} - {}'.format(f, fname)
    all_describes = pd.DataFrame(all_describes)
    dt = datetime.datetime.utcnow().isoformat()
    all_describes.to_csv('btax_regress_{}.csv'.format(dt))
    return all_describes


def run_regression_once(start_year, iit_reform, **user_params):
    diffs = run_test()
    return deltas(diffs)




