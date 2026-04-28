def create_sqlite_table(cur):
    """
    Creates a sqlite table. The combination of input file and output file
    must be unique for each entry. If a different output file exists for the same input file,
    the associated git commit hash is necessarily different.
    :param cur: Cursor object for the SQLite connection
    """
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS alara_simulations (
        id TEXT PRIMARY KEY,
        input_file TEXT,
        output_file TEXT,
        flux_file TEXT,
        git_hash TEXT,
        UNIQUE(input_file, output_file)
        )
    """
    )

def populate_table(cur, data_dict):
    """
    Populate the sqlite table with data.
    :param cur: Cursor object for the SQLite connection
    :param data_dict: dictionary containing information for the database, with structure:
    {
        "id": iterable of str/int,
        "input_file": iterable of str,
        "output_file": iterable of str,
        "flux_file": iterable of str,
        "git_hash": iterable of str,
    }
    """

    cur.executemany(
        "INSERT INTO alara_simulations (id, input_file, output_file, flux_file, git_hash) VALUES (?, ?, ?, ?, ?)",
        list(zip(*data_dict.values())),
    )
