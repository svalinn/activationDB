import json

def find_flux_spec_shape_id(sqlite_conn, column_name, row_value):
    '''
    Assuming that a table called flux_spectra exists in the database, find
    the id of the desired flux spectrum from the table. Assumes that the
    spectral data in the table is stored in json/text format.
    :param: sqlite_conn (sqlite3 connection object)
    :param: column_name (str, one of "flux_spectrum" or "flux_file")
    :param: row_value: value taken on by either the flux_spectrum or flux_file columns,
                        one of the following:
        - flux spectrum shape (iterable, normalized flux spectrum with the number of entries 
                            being the number of groups in the structure)
        - flux file (str, path to file containing flux spectrum)
    '''
    if column_name == 'flux_spectrum':
        db_value = json.dumps(row_value.tolist()) if hasattr(row_value, "tolist") else json.dumps(row_value)
        result = sqlite_conn.execute(
        f"SELECT flux_spec_shape_id FROM flux_spectra WHERE json({column_name}) = json(?)",
        (db_value,)
        )
    elif column_name == 'flux_file':
        result = sqlite_conn.execute(
        f"SELECT flux_spec_shape_id FROM flux_spectra WHERE {column_name} = ?",
        (row_value,)
        )
    flux_spec_shape_id = result.fetchone()[0]
    return flux_spec_shape_id