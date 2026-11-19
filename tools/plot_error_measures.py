import numpy as np
import yaml
import matplotlib.pyplot as plt
from scipy.stats import ecdf
from calculate_nuclide_error import prep_arrays_for_measures, create_error_measures
from pathlib import Path
import argparse


def make_plotting_errors(scoring_metric, err_measures):
    if scoring_metric == "child_sum_ratio":
        measure_error = np.abs(err_measures['child_sum_ratio'] - 1)

    elif scoring_metric == "norm_abs_diff":
        measure_error = err_measures['norm_abs_diff']

    elif scoring_metric == "cosine_similarity":
        measure_error = 1 - err_measures[
            'cosine_similarity']  # Number densities cannot be negative, so this is a measure \
            # of the deviation from the ideal value of cosine_similarity=1

    elif scoring_metric == "norm_rel_diff":
        measure_error = err_measures['norm_rel_diff']
    return measure_error


def make_x_label_strings(scoring_metric):
    if scoring_metric == "child_sum_ratio":
        x_label_string = r'$|\mathrm{Child Sum \ Ratio} - 1|$'
    elif scoring_metric == "norm_abs_diff":
        x_label_string = r'$\mathrm{Norm\ Absolute\ Difference}$'
    elif scoring_metric == "cosine_similarity":
        x_label_string = r'$\mathrm{1 - Cosine\ Similarity}$'
    elif scoring_metric == "norm_rel_diff":
        x_label_string = r'$\mathrm{Norm\ Relative\ Difference}$'
    return x_label_string


def make_step_plots(step_axes,
                    x_label_string,
                    y_label_string,
                    title_str,
                    plot_path_name,
                    log_x=False):
    plt.figure()
    plt.step(*step_axes, where='post')
    if log_x:
        plt.xscale('log')
    plt.xlabel(x_label_string)
    plt.ylabel(y_label_string)
    plt.title(title_str)
    plt.grid(True)
    plt.savefig(plot_path_name)
    plt.close()


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--yaml',
        '-y',
        default="prep_sql_for_ml_model.yaml",
        help="Path (str) to YAML containing information used to train models")
    
    parser.add_argument(
        '--plot_folder',
        '-f',
        default="knn_joblib_npz_pre_approximation_measures_plots",
        help="Path (str) to folder all plots will be saved to")

    parser.add_argument(
        '--parent_nuc',
        '-n',
        type=str,
        required=True,
        help="Parent nuclide (str) to plot results for. The chemical symbol and mass number must be" \
        "separated either by a colon or hyphen (-)")

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
    yaml_arg = args.yaml
    plot_folder = args.plot_folder
    inputs = read_yaml(yaml_arg)

    parent_nuc = args.parent_nuc
    
    for scoring_metric in [
            "child_sum_ratio", "norm_abs_diff", "cosine_similarity",
            "norm_rel_diff"
    ]:
        with open('prep_sql_for_ml_model.yaml', 'r') as yaml_file:
            inputs = yaml.safe_load(yaml_file)
        filename = f"{parent_nuc}_knn_{scoring_metric}_test_results.npz"
        with np.load(filename) as data:
            # Y_test is already filtered by nonzero_child_indices, and \
            # by construction Y_pred has the same size as Y_test
            true_densities = data['Y_test']
            predicted_densities = data['Y_pred']
            nonzero_child_indices = data['nonzero_child_indices']

        child_nucs = inputs['child_nucs']
        retained_child_nucs = [
            child_nucs[nonzero_idx] for nonzero_idx in nonzero_child_indices
        ]

        response_sum_p_removed, rel_sample_responses_p_removed = prep_arrays_for_measures(
            parent_nuc.replace(":","-"), retained_child_nucs,
            predicted_densities, true_densities)
        err_measures = create_error_measures(response_sum_p_removed,
                                             rel_sample_responses_p_removed)

        measure_error = make_plotting_errors(scoring_metric, err_measures)

        ecdf_valid_mask = np.isfinite(measure_error)
        measure_error = measure_error[ecdf_valid_mask]
        ecdf_measure = ecdf(measure_error)

        sample_total_true_densities = np.sum(true_densities,
                                             axis=1)[ecdf_valid_mask]

        sorted_indices = np.argsort(measure_error)
        sorted_errors = measure_error[sorted_indices]
        sorted_densities = sample_total_true_densities[sorted_indices]

        cumulative_density_fraction = (np.cumsum(sorted_densities) /
                                       np.sum(sample_total_true_densities))
        step_axes = [[
            ecdf_measure.cdf.quantiles, ecdf_measure.cdf.probabilities
        ], [sorted_errors, cumulative_density_fraction]]

        x_label_string = make_x_label_strings(scoring_metric)
        y_label_strings = [
            'Cumulative fraction of samples',
            'Cumulative fraction of total number density'
        ]

        title_strs = [
            f'{parent_nuc} {scoring_metric} Error ECDF',
            f'{parent_nuc} {scoring_metric} Number Density-Weighted Error ECDF'
        ]

        plot_path_names = [
            Path(
                f'{plot_folder}/{parent_nuc.replace(":","-")}_{scoring_metric}_sample_ecdf.png'
            ),
            Path(
                f'{plot_folder}/{parent_nuc.replace(":", "-")}_{scoring_metric}_weighted_sample_ecdf.png'
            )
        ]

        for step_axes, y_label_string, title_str, plot_path_name in zip(
                step_axes, y_label_strings, title_strs, plot_path_names):
            make_step_plots(step_axes,
                            x_label_string,
                            y_label_string,
                            title_str,
                            plot_path_name,
                            log_x=False)
            log_x_plot_path_name = plot_path_name.with_stem(
                plot_path_name.stem + '_log_x')
            make_step_plots(step_axes,
                            x_label_string,
                            y_label_string,
                            title_str,
                            log_x_plot_path_name,
                            log_x=True)


if __name__ == "__main__":
    main()
