import pytest

from btax.run_btax import run_btax_to_json_tables

pytest_args = []
tables = run_btax_to_json_tables(test_run=True,
                                 start_year=2016,
                                 iit_reform={},
                                 btax_betr_corp=0.2,
                                 btax_betr_entity_Switch=True,
                                 btax_betr_pass=.3)
for k, item in tables.items():
    for rbc, table in item.items():
        pytest_args.append((k, rbc, table))

@pytest.mark.needs_puf
@pytest.mark.parametrize('industry_or_asset,changed_reform_base,table', pytest_args)
def test_correct_number_of_cols(industry_or_asset, changed_reform_base, table):
    '''Test that each table row has 7 elements where the first is a string
    and others are floats or ints'''
    if industry_or_asset == 'industry_d':
        expected_cols = 7
    else:
        expected_cols = 7
    lens = set(map(len, table[1:]))
    most_lens = tuple(lens)[0]
    assert len(lens) == 1 and most_lens == expected_cols and len(table[0]) == most_lens - 1

    for row in table[1:]:
        assert isinstance(row[0], (str, unicode))
        assert all(tuple(isinstance(r, (int, float)) for r in row[1:]))
