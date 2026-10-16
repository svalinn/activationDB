from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
)
from sklearn.model_selection import GridSearchCV, train_test_split

from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

import joblib
import prepare_sql_adf_for_ml_model
import extract_sql_data
import sqlite3
import argparse
import yaml
import polars as pl
import numpy as np

def optimize_estimator_hyperparams(X_train, Y_train):

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("regressor", KNeighborsRegressor()),
    ])

    params = {
        "scaler": [
            StandardScaler(),
            MinMaxScaler(),
            RobustScaler(),
        ],
        "regressor__n_neighbors": [1, 3, 5, 10, 20],
        "regressor__weights": ["uniform", "distance"],
        "regressor__p": [1, 2],
    }

    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=params,
        cv=5,
        scoring="neg_mean_squared_error",
        n_jobs=-1,
        pre_dispatch="n_jobs",
        verbose=2,
    )

    grid_search.fit(X_train, Y_train)

    return grid_search


def save_optimized_model(grid_search, parent_nuc, nonzero_child_indices):

    joblib.dump(
        {
            "model": grid_search.best_estimator_,
            "parent_nuc": parent_nuc,
            "nonzero_child_indices": nonzero_child_indices,
        },
        f"{parent_nuc}_knn_model.joblib",
    )

    joblib.dump(
        grid_search,
        f"{parent_nuc}_grid_search_results.joblib",
    )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--model_training_yaml',
        '-t',
        help="Path (str) to YAML containing information to train models")

    parser.add_argument('--use_stored_df',
                        '-u',
                        action='store_true',
                        help="Use a df saved as .csv to train models")

    parser.add_argument('--parent_idx',
                        '-p',
                        type=int,
                        required=True,
                        help="Index of the parent nuclide to train")

    args = parser.parse_args()

    return args


def read_yaml(yaml_arg):
    '''
    input:
        yaml_arg : output of parse_args() corresponding to
                   args.model_training_yaml
    '''

    with open(yaml_arg, 'r') as yaml_file:
        inputs = yaml.safe_load(yaml_file)

    return inputs


def main():

    args = parse_args()

    inputs = read_yaml(args.model_training_yaml)

    filter_str = inputs['filter_str']
    db_name = inputs['db_name']
    batch_size = inputs['batch_size']
    child_nucs = inputs['child_nucs']
    parent_nucs = inputs['parent_nucs']

    parent_idx = args.parent_idx
    parent_nuc = parent_nucs[parent_idx]
    df_csv_name = inputs['df_csv_name']

    text_file = open(f'knn_per_parent_{parent_nuc}_prints.txt', 'w')

    conn = sqlite3.connect(db_name)

    dict_df = extract_sql_data.make_dict_from_small_table(conn)

    if args.use_stored_df:
        partial_training_df = pl.read_csv(df_csv_name,
                                          schema_overrides={
                                              'nuclide': pl.Enum(child_nucs),
                                              'run_lbl': pl.Categorical,
                                              'block_name':
                                              pl.Enum(parent_nucs),
                                              'flux_spec_shape_id': pl.UInt8
                                          })

    else:

        partial_training_df = (extract_sql_data.make_df_from_num_dens_table(
            conn, filter_str, batch_size, child_nucs, parent_nucs))

        partial_training_df = pl.concat([df for df in partial_training_df])

        partial_training_df.write_csv(df_csv_name)

    conn.close()

    X_train, Y_train = (
        prepare_sql_adf_for_ml_model.make_features_outputs_per_parent(
            partial_training_df, dict_df, child_nucs, parent_nucs, parent_idx))

    X_train, X_test, Y_train, Y_test_full = train_test_split(
        X_train,
        Y_train,
        test_size=0.20,
        random_state=42,
        shuffle=True,
    )

    original_y_shape = Y_train.shape
    nonzero_child_indices = np.flatnonzero(np.any(Y_train != 0, axis=0))
    zero_child_indices = np.flatnonzero(np.all(Y_train == 0, axis=0))
    removed_parent_child = []
    for child_idx in zero_child_indices:
        removed_parent_child.append((parent_nuc, child_nucs[child_idx]))

    Y_train = Y_train[:, nonzero_child_indices]
    Y_test = Y_test_full[:, nonzero_child_indices]

    print(f"Parent: {parent_nuc}", file=text_file)
    print(f"Training samples: {X_train.shape[0]}", file=text_file)
    print(f"Testing samples: {X_test.shape[0]}", file=text_file)
    print(f"Original training Y shape: {original_y_shape}",
          file=text_file)
    print(f"Number of nonzero children: " f"{len(nonzero_child_indices)}", file=text_file)
    print(f"Number of zero children removed: " f"{len(zero_child_indices)}", file=text_file)
    print(f"Final Y shape: {Y_train.shape}", file=text_file)
    print(f"Final testing Y shape: {Y_test.shape}",
        file=text_file)

    grid_search = optimize_estimator_hyperparams(X_train, Y_train)
    best_model = grid_search.best_estimator_
    Y_pred = best_model.predict(X_test)

    mae = mean_absolute_error(Y_test, Y_pred)
    mse = mean_squared_error(Y_test, Y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(Y_test, Y_pred)

    print(f"Test MAE:  {mae:.6e}", file=text_file)
    print(f"Test MSE:  {mse:.6e}", file=text_file)
    print(f"Test RMSE: {rmse:.6e}", file=text_file)
    print(f"Test R2:   {r2:.6e}", file=text_file)

    child_mae = np.mean(
        np.abs(Y_test - Y_pred), axis=0
    )

    child_rmse = np.sqrt(
        np.mean((Y_test - Y_pred) ** 2, axis=0)
    )

    retained_child_nucs = [
        child_nucs[i] for i in nonzero_child_indices
    ]

    metrics_df = pl.DataFrame({
        "child_nuc": retained_child_nucs,
        "MAE": child_mae,
        "RMSE": child_rmse,
    })

    metrics_df.write_csv(
        f"{parent_nuc}_knn_test_metrics.csv"
    )

    np.savez_compressed(
        f"{parent_nuc}_knn_test_results.npz",
        Y_test=Y_test,
        Y_pred=Y_pred,
        nonzero_child_indices=nonzero_child_indices,
        test_mae=mae,
        test_mse=mse,
        test_rmse=rmse,
        test_r2=r2,
    )


    save_optimized_model(grid_search, parent_nuc, nonzero_child_indices)

    removed_filename = (f"{parent_nuc}_removed_parent_child_combinations.npy")

    np.save(removed_filename, np.array(removed_parent_child, dtype=object))

if __name__ == "__main__":
    main()
