import json

import pandas as pd

from analyst.data import Dataset


def _col(profile, name):
    return next(c for c in profile["columns"] if c["name"] == name)


def test_profile_counts(tiny_ds):
    p = tiny_ds.profile()
    json.dumps(p)  # JSON-safe
    assert p["row_count"] == 5
    assert p["column_count"] == 4
    assert p["duplicate_rows"] == 1
    units = _col(p, "units")
    assert units["kind"] == "numeric"
    assert units["null_count"] == 1
    assert units["min"] == 2 and units["max"] == 6
    assert units["mean"] == 4.5
    assert sum(b["count"] for b in units["histogram"]) == 4
    region = _col(p, "region")
    assert region["kind"] == "categorical"
    assert region["top_values"][0] == {"value": "S", "count": 3}
    assert _col(p, "date")["kind"] == "datetime"
    assert len(p["sample_rows"]) == 5


def test_load_csv_with_na_strings(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("a,b,c\n1,NA,2024-01-01\n2,3.5,2024-02-01\nNA,4,2024-03-01\n")
    ds = Dataset.from_path(f)
    assert ds.kinds == {"a": "numeric", "b": "numeric", "c": "datetime"}
    p = ds.profile()
    assert _col(p, "a")["null_count"] == 1


def test_load_xlsx(tmp_path):
    f = tmp_path / "x.xlsx"
    pd.DataFrame({"k": ["a", "b"], "v": [1, 2]}).to_excel(f, index=False)
    ds = Dataset.from_path(f)
    assert ds.row_count == 2 and ds.kinds["v"] == "numeric"
