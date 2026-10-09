import pytest
import pandas as pd
import create_adf

@pytest.fixture
def make_lbl_path_dict():
    lbl_path_dict = {"pytest_alara_b" : "../pytest_support_files/pytest_alara_out_b",
                     "pytest_alara_c" : "../pytest_support_files/pytest_alara_out_c"}
    return lbl_path_dict


@pytest.fixture
def make_df_dicts():
    df_dicts = [{
                "time": [-1]*7 + [0.0000e+00]*7,
                "time_unit": ['s']*14,
                "nuclide": ['h-3', 'li-8', 'be-8', 'be-10', 'be-11', 'b-12', 'total']*2,
                "half_life":[3.8911e+08, 8.4200e-01, 7.0000e-17, 5.0492e+13, 1.3810e+01, 2.0200e-02, 0.0000e+00]*2,
                "run_lbl":['pytest_alara_b']*14,
                "block": [1]*14,
                "block_name": ["zone_1"]*14,
                "block_num": [1]*14,
                "variable": [1]*14,
                "var_unit": ["Bq/cm3"]*14,
                "value": [0.0000e+00]*7 + [7.0433e+11, 3.8339e+12, 3.8339e+12, 5.1096e+06, 5.9495e+11, 3.0033e+11, 9.2675e+12]
                },
                {
                "time": [-1]*6 + [0.0000e+00]*6,
                "time_unit": ['s']*12,
                "nuclide": ['h-3', 'be-10', 'b-12', 'b-13', 'c-14', 'total']*2,
                "half_life":[3.8911e+08, 5.0492e+13, 2.0200e-02, 1.7400e-02, 1.8082e+11, 0.0000e+00]*2,
                "run_lbl":['pytest_alara_c']*12,
                "block": [1]*12,
                "block_name": ["zone_1"]*12,
                "block_num": [1]*12,
                "variable": [1]*12,
                "var_unit": ["Bq/cm3"]*12,
                "value": [0.0000e+00]*6 + [3.6107e+09, 5.1420e+05, 3.1832e+09, 9.1136e+09, 1.4456e+06, 1.5909e+10]
                }]
    return df_dicts


@pytest.fixture
def make_mult_pdfs(make_df_dicts):
    pdf_list = []
    for df_dict in make_df_dicts:
        pdf = pd.DataFrame(df_dict)
        pdf_list.append(pdf)
    return pdf_list

def test_generate_single_adf(make_lbl_path_dict, make_mult_pdfs):
    for (run_lbl, output_filepath), make_single_pdf in zip(make_lbl_path_dict.items(), 
                                                            make_mult_pdfs):
        adf = create_adf.generate_single_adf(run_lbl, output_filepath)
        adf = adf.sort_values(by=adf.columns.tolist()).reset_index(drop=True)
        make_single_pdf = make_single_pdf.sort_values(by=make_single_pdf.columns.tolist()).reset_index(drop=True)
        # adf = alara_output_processing.ALARADFrame, pdf = pd.DataFrame
        pd.testing.assert_frame_equal(adf, make_single_pdf, check_frame_type=False)


def test_generate_adfs_from_dict(make_lbl_path_dict, make_mult_pdfs):
    adf_list = create_adf.generate_adfs_from_dict(make_lbl_path_dict)
    pdf_list = make_mult_pdfs
    for adf, pdf in zip(adf_list, pdf_list):
        adf = adf.sort_values(by=adf.columns.tolist()).reset_index(drop=True)
        pdf = pdf.sort_values(by=adf.columns.tolist()).reset_index(drop=True)
        pd.testing.assert_frame_equal(adf, pdf, check_frame_type=False)

    