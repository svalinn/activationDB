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
            sqlite3.connect(":memory:").cursor().execute(
                """
                CREATE TABLE alara_simulations (
                id TEXT PRIMARY KEY,
                input_file TEXT,
                output_file TEXT,
                flux_file TEXT,
                git_hash TEXT,
                UNIQUE(input_file, output_file)
                )
                """
            ),
            {
                "id": [str(uuid.uuid4()), 5],
                "input_file": ["inp_1", "inp_2"],
                "output_file": ["out_5", "out_7"],
                "flux_file": ["f_2", "f_3"],
                "git_hash": ["gh_5", "gh_7"],
            },
        ),
    ],
)
def test_populate_table(cur, data_dict):
    """
    Ensure that the "INSERT into" statement was executed successfully,
    without committing the operation into the actual database.
    """
    cur.execute("BEGIN") # stops subsequent statements (e.g. CREATE TABLE) from being committed automatically
    ab.create_sqlite_table(cur)
    ab.populate_table(cur, data_dict)
    rows = cur.execute("SELECT * from alara_simulations").fetchall()
    assert len(rows) == len(data_dict["id"])
    cur.connection.close()
