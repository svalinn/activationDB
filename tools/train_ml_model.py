from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
)
from sklearn.linear_model import Ridge

import joblib
import prepare_sql_adf_for_ml_model
import extract_sql_data
import sqlite3
import argparse
import yaml
import polars as pl

models = {
    "knn": {
        "pipeline":
        Pipeline([("scaler", StandardScaler()),
                  ("regressor", KNeighborsRegressor())]),
        "params": {
            "scaler": [StandardScaler(),
                       MinMaxScaler(),
                       RobustScaler()],
            "regressor__n_neighbors": [1, 3, 5, 10, 20],
            "regressor__weights": ["uniform", "distance"],
            "regressor__p": [1, 2]
        }
    },
    "ridge": {
        "pipeline":
        Pipeline([("scaler", StandardScaler()), ("regressor", Ridge())]),
        "params": {
            "scaler": [StandardScaler(),
                       MinMaxScaler(),
                       RobustScaler()],
            "regressor__alpha": [0.01, 0.1, 1.0, 10.0, 100.0]
        }
    },
    "random_forest": {
        "pipeline":
        Pipeline([("regressor", RandomForestRegressor(n_jobs=1,
                                                      random_state=1))]),
        "params": {
            "regressor__n_estimators": [100, 200],
            "regressor__max_depth": [None, 10, 20],
            "regressor__min_samples_leaf": [1, 2, 5]
        }
    },
    "extra_trees": {
        "pipeline":
        Pipeline([("regressor", ExtraTreesRegressor(n_jobs=1,
                                                    random_state=1))]),
        "params": {
            "regressor__n_estimators": [100, 200],
            "regressor__max_depth": [None, 10, 20],
            "regressor__min_samples_leaf": [1, 2, 5]
        }
    }
}


def optimize_estimator_hyperparams(X_train, Y_train_flat):
    results = {}

    for regressor_name, model_info in models.items():
        grid_search = GridSearchCV(estimator=model_info["pipeline"],
                                   param_grid=model_info["params"],
                                   cv=5,
                                   scoring="neg_mean_squared_error",
                                   n_jobs=-1,
                                   pre_dispatch="n_jobs",
                                   verbose=2)

        grid_search.fit(X_train, Y_train_flat)
        results[regressor_name] = grid_search

    return results


def save_optimized_model(results):
    for regressor_name, grid_search in results.items():
        fileregressor_name = f"{regressor_name}_model.joblib"

        joblib.dump(grid_search.best_estimator_, fileregressor_name)

    joblib.dump(results, "regressor_grid_search_results.joblib")


def evaluate_and_save_errors(results, X_test, Y_test_flat):
    summary = []
    test_errors = {}

    with open("regressors_matrix_prints.txt", "w") as print_file:
        for regressor_name, grid_search in results.items():
            best_model = grid_search.best_estimator_
            Y_pred = best_model.predict(X_test)

            signed_errors = Y_test_flat - Y_pred
            absolute_errors = abs(signed_errors)
            squared_errors = signed_errors**2

            mae = mean_absolute_error(Y_test_flat, Y_pred)
            mse = mean_squared_error(Y_test_flat, Y_pred)
            rmse = mse**0.5
            r2 = r2_score(Y_test_flat, Y_pred)

            summary.append({
                "model": regressor_name,
                "best_params": str(grid_search.best_params_),
                "MAE": mae,
                "MSE": mse,
                "RMSE": rmse,
                "R2": r2
            })

            test_errors[regressor_name] = {
                "predictions": Y_pred,
                "actual_values": Y_test_flat,
                "signed_errors": signed_errors,
                "absolute_errors": absolute_errors,
                "squared_errors": squared_errors,
                "metrics": {
                    "MAE": mae,
                    "MSE": mse,
                    "RMSE": rmse,
                    "R2": r2
                }
            }

            metrics_text = (f"\n{regressor_name}\n"
                            f"Best parameters: {grid_search.best_params_}\n"
                            f"MAE:  {mae}\n"
                            f"MSE:  {mse}\n"
                            f"RMSE: {rmse}\n"
                            f"R2:   {r2}\n")

            print(metrics_text)
            print_file.write(metrics_text)

    pl.DataFrame(summary).write_csv("test_error_summary.csv")
    joblib.dump(test_errors, "test_errors.joblib")


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

    args = parser.parse_args()
    return args


def read_yaml(yaml_arg):
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

    conn = sqlite3.connect(db_name)
    dict_df = extract_sql_data.make_dict_from_small_table(conn)

    if args.use_stored_df:
        partial_training_df = pl.read_csv("selected_df.csv",
                                          schema_overrides={
                                              'nuclide': pl.Enum(child_nucs),
                                              'run_lbl': pl.Categorical,
                                              'block_name':
                                              pl.Enum(parent_nucs),
                                              'flux_spec_shape_id': pl.UInt8,
                                          })
    else:
        partial_training_df = extract_sql_data.make_dfs_from_num_dens_table(
            conn, filter_str, batch_size, child_nucs, parent_nucs)

        partial_training_df = pl.concat([df for df in partial_training_df])

        partial_training_df.write_csv("selected_df.csv")

    conn.close()

    X, Y = prepare_sql_adf_for_ml_model.make_features_outputs(
        partial_training_df, dict_df, child_nucs, parent_nucs)

    Y = Y.reshape(Y.shape[0], -1)

    X_train, X_test, Y_train, Y_test = train_test_split(X,
                                                        Y,
                                                        test_size=0.2,
                                                        random_state=42)

    print(f"Training samples: {X_train.shape[0]}")
    print(f"Test samples:     {X_test.shape[0]}")
    print(f"Number of inputs: {X_train.shape[1]}")
    print(f"Number of outputs: {Y_train.shape[1]}")

    results = optimize_estimator_hyperparams(X_train, Y_train)

    save_optimized_model(results)

    evaluate_and_save_errors(results, X_test, Y_test)


if __name__ == "__main__":
    main()
