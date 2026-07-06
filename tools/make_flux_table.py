def create_flux_table(cur):
    """
    Creates a sqlite table called flux_spectra using a provided sqlite cursor object.
    :param: cur (sqlite cursor object)

    flux_spec_shape_id is an alias for the table's internal rowid column
    """
    cur.execute("""CREATE TABLE IF NOT EXISTS flux_spectra (
    flux_spec_shape_id INTEGER PRIMARY KEY,
    flux_file TEXT,
    flux_spectrum TEXT,                           
    UNIQUE(flux_file, flux_spectrum)
    )
    """
    )
  
def populate_flux_table(cur, flux_data_dict):
    """
    Populates a flux table that has already been initialized with data used to identify each spectrum.
    :param: cur (sqlite cursor object that points to a connection with a table called flux_spectra)
    :param: flux_data_dict (dictionary with the form below)
    {
    'flux_file' : (str, path to file containing flux spectrum),
    'flux_spectrum' : (str, iterable of flux values for some group structure, stored as text)
    }
    """
    cur.executemany(
            "INSERT INTO flux_spectra (flux_file, flux_spectrum) VALUES (?, ?)",
            list(zip(*flux_data_dict.values())),
    )