import pytest
import alara_bookkeeping as ab
import sqlite3
import uuid

@pytest.mark.parametrize(
    "cur,data_dict,exp_foreign_keys",
    [
        (
            sqlite3.connect(":memory:").cursor().executescript(
                """
                PRAGMA foreign_keys=ON;
                CREATE TABLE flux_spectra (
                flux_file TEXT UNIQUE
                );
                INSERT INTO flux_spectra (flux_file) VALUES ('f_2');
                INSERT INTO flux_spectra (flux_file) VALUES ('f_3');
                CREATE TABLE alara_simulations (
                run_lbl TEXT PRIMARY KEY,
                input_file TEXT,
                output_file TEXT,
                flux_file TEXT,
                git_hash TEXT,
                UNIQUE(input_file, output_file),
                FOREIGN KEY (flux_file) REFERENCES flux_spectra(flux_file)
                );
                """
                ),
            {
                "run_lbl": [str(uuid.uuid4()), 5],
                "input_file": ["inp_1", "inp_2"],
                "output_file": ["out_5", "out_7"],
                "flux_file": ["f_2", "f_3"],
                "git_hash": ["gh_5", "gh_7"],
            },
            [(0, 0, 'flux_spectra', 'flux_file', 'flux_file', 'NO ACTION', 'NO ACTION', 'NONE')]
        ),
    ],
)
def test_populate_table(cur, data_dict, exp_foreign_keys):
    """
    Ensure that the "INSERT into" statement was executed successfully.
    """
    ab.create_sqlite_table(cur)
    ab.populate_table(cur, data_dict)
    rows = cur.execute("SELECT * from alara_simulations").fetchall()
    obs_foreign_keys = cur.execute(
    """
    PRAGMA foreign_key_list('alara_simulations')
    """
    ).fetchall()
    assert len(rows) == len(data_dict["run_lbl"])
    assert obs_foreign_keys == exp_foreign_keys
    cur.connection.close()
