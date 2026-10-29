import numpy as np
import polars as pl


def make_features_outputs(partial_training_df, dict_df, child_nucs,
                                   parent_nucs, approx_name=None):

    out_arr_list = []
    feature_arr_list = []

    for run_lbl in partial_training_df["run_lbl"].unique():

        parent_child_nuc_arr = np.zeros((len(child_nucs), len(parent_nucs)))

        reduced_df = partial_training_df.filter(pl.col("run_lbl") == run_lbl)

        for df_row in reduced_df.iter_rows(named=True):

            child_nuc = df_row["nuclide"]
            parent_nuc = df_row["block_name"]

            parent_child_nuc_arr[
                child_nucs.index(child_nuc),
                parent_nucs.index(parent_nuc)] = df_row["num_dens_(atoms/cm3)"]
            if approx_name == "flattening":
                t_irr = df_row['t_irr_flat']
            elif approx_name == "compression":
                t_irr = df_row['t_irr_compressed']
            else:    
                t_irr = df_row['t_irr']
            avg_flux_mag = df_row["avg_flux_mag"]

            flux_spec_shape = eval(dict_df[df_row["flux_spec_shape_id"]])

        # Each run_lbl is associated with a single combination of each of the features
        feature_arr_list.append(
            np.array((t_irr, avg_flux_mag, *flux_spec_shape)))

        out_arr_list.append(parent_child_nuc_arr)
    return np.array(feature_arr_list), np.array(out_arr_list)


def make_features_outputs_per_parent(partial_training_df, dict_df,
                                              child_nucs, parent_nucs,
                                              parent_idx, approx_name=None):

    parent = parent_nucs[parent_idx]

    all_features = []
    all_out = []

    partial_training_df = partial_training_df.filter(
        pl.col("block_name") == parent)

    for run_lbl in partial_training_df["run_lbl"].unique():

        parent_run_reduced_df = partial_training_df.filter(
            pl.col("run_lbl") == run_lbl)

        child_num_dens = np.zeros(len(child_nucs))

        for df_row in parent_run_reduced_df.iter_rows(named=True):

            child_idx = child_nucs.index(df_row["nuclide"])

            child_num_dens[child_idx] = (df_row["num_dens_(atoms/cm3)"])

        flux_spec_shape = eval(dict_df[df_row["flux_spec_shape_id"]])
        if approx_name == "flattening":
            t_irr = df_row['t_irr_flat']
        elif approx_name == "compression":    
            t_irr = df_row['t_irr_compressed']
        else:
            t_irr = df_row["t_irr"]    
        run_features = np.array(
            (t_irr, df_row["avg_flux_mag"], *flux_spec_shape))

        all_features.append(run_features)
        all_out.append(child_num_dens)

    return (np.array(all_features), np.array(all_out))
