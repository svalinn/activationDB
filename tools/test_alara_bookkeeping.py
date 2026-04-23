import pytest
import alara_bookkeeping as ab
import sqlite3
import uuid


@pytest.mark.parametrize(
    "cur,data_dict",
    [
        (
            sqlite3.connect("activation_results.db").cursor(),
            {
                "id": [str(uuid.uuid4()), str(uuid.uuid4())],
                "input_file": ["inp_1", "inp_2"],
                "output_file": ["out_1", "out_2"],
                "flux_file": ["f_1", "f_2"],
                "git_hash": ["gh_1", "gh_2"],
            },
        ),
        (
            sqlite3.connect("activation_results.db").cursor(),
            {
                "id": [1, 2],
                "input_file": ["inp_1", "inp_2"],
                "output_file": ["out_1", "out_2"],
                "flux_file": ["f_1", "f_2"],
                "git_hash": ["gh_1", "gh_2"],
            },
        ),
        (
            sqlite3.connect(":memory:").cursor(),
            {
                "id": [str(uuid.uuid4()), 5],
                "input_file": ["inp_1", "inp_2"],
                "output_file": ["out_1", "out_2"],
                "flux_file": ["f_1", "f_2"],
                "git_hash": ["gh_1", "gh_2"],
            },
        ),
    ],
)
def test_populate_table(cur, data_dict):
    """
    Ensure that the "INSERT into" statement was executed successfully,
    without committing the operation into the actual database.
    """
    ab.populate_table(cur, data_dict)
    rows = cur.execute("SELECT * from alara_simulations").fetchall()
    assert len(rows) == len(data_dict["id"])
    cur.connection.close()
