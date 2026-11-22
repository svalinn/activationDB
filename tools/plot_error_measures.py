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
        x_label_string = r'$|\mathrm{Child\ Sum \ Ratio} - 1|$'
    elif scoring_metric == "norm_abs_diff":
        x_label_string = r'$\mathrm{Norm\ Absolute\ Difference}$'
    elif scoring_metric == "cosine_similarity":
        x_label_string = r'$\mathrm{1 - Cosine\ Similarity}$'
    elif scoring_metric == "norm_rel_diff":
        x_label_string = r'$\mathrm{Norm\ Relative\ Difference}$'
    return x_label_string


def make_step_plots(plot_label,
                    x_label_string,
                    y_label_string,
                    title_str,
                    plot_path_name,
                    log_x=False,
                    step_axes=None):
    if step_axes is not None:
        plt.figure()
        plt.step(*step_axes, where='post', label=plot_label)
    if log_x:
        plt.xscale('log')
    plt.xlabel(x_label_string)
    plt.ylabel(y_label_string)
    plt.title(title_str)
    plt.grid(True)
    plt.tight_layout()
    plt.legend(loc='best', fontsize=5)
    plt.savefig(plot_path_name)
    plt.close()


def calculate_per_child_child_sum_ratios(predicted_densities, true_densities,
                                         parent_nuc, retained_child_nucs):
    '''
    This function calculates the child-sum ratio for each child nuclide. This ratio represents the number density of
    the child divided by the sum of number densities over all samples for that child nuclide. It differs from the
    calculation of the regular child-sum ratio as the denominator is the total number density of a single child and
    not the total number density of all the nuclides.
    '''
    child_sum_ratios = np.ndarray((len(retained_child_nucs)), dtype=object)
    parent_in_children_idx = retained_child_nucs.index(parent_nuc)
    for child_nuc_idx, child_nuc in enumerate(retained_child_nucs):
        child_response_sum_p_removed, child_rel_sample_responses_p_removed = prep_arrays_for_measures(
            parent_nuc, [child_nuc, parent_nuc],
            predicted_densities[:, [child_nuc_idx, parent_in_children_idx]],
            true_densities[:, [child_nuc_idx, parent_in_children_idx]])
        child_sum_ratios[child_nuc_idx] = create_error_measures(
            child_response_sum_p_removed,
            child_rel_sample_responses_p_removed)['child_sum_ratio']
    child_sum_ratios = np.delete(child_sum_ratios, parent_in_children_idx)
    child_sum_ratios = {"child_sum_ratio": np.column_stack(child_sum_ratios)}
    return child_sum_ratios


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

    for scoring_metric in [
            "child_sum_ratio", "norm_abs_diff", "cosine_similarity",
            "norm_rel_diff"
    ]:
        parent_nuc = args.parent_nuc
        with open('prep_sql_for_ml_model.yaml', 'r') as yaml_file:
            inputs = yaml.safe_load(yaml_file)
        filename = f"{parent_nuc}_knn_{scoring_metric}_test_results.npz"
        with np.load(filename) as data:
            # Y_test is already filtered by nonzero_child_indices, and \
            # by construction Y_pred has the same size as Y_test
            true_densities = np.array(data['Y_test'])
            predicted_densities = np.array(data['Y_pred'])
            nonzero_child_indices = data['nonzero_child_indices']
        child_nucs = inputs['child_nucs']
        retained_child_nucs = [
            child_nucs[nonzero_idx] for nonzero_idx in nonzero_child_indices
        ]

        parent_nuc = parent_nuc.replace(":", "-")
        response_sum_p_removed, rel_sample_responses_p_removed = prep_arrays_for_measures(
            parent_nuc, retained_child_nucs, predicted_densities,
            true_densities)
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
            Path(f'{plot_folder}/{parent_nuc}_{scoring_metric}_sample_ecdf.png'
                 ),
            Path(
                f'{plot_folder}/{parent_nuc}_{scoring_metric}_weighted_sample_ecdf.png'
            )
        ]

        for y_label_string, title_str, plot_path_name, step_axis_list in zip(
                y_label_strings, title_strs, plot_path_names, step_axes):
            make_step_plots(f'{scoring_metric} ECDF',
                            x_label_string,
                            y_label_string,
                            title_str,
                            plot_path_name,
                            log_x=None,
                            step_axes=step_axis_list)
            log_x_plot_path_name = plot_path_name.with_stem(
                plot_path_name.stem + '_log_x')
            make_step_plots(
                f'{scoring_metric} Overall Number-Density Weighted ECDF',
                x_label_string,
                y_label_string,
                title_str,
                log_x_plot_path_name,
                log_x=True,
                step_axes=step_axis_list)

        sorted_child_densities = true_densities[ecdf_valid_mask][
            sorted_indices, :]

        cumulative_child_density_fractions = np.divide(
            (np.cumsum(sorted_child_densities, axis=0)),
            (np.sum(sorted_child_densities, axis=0)),
            out=np.full_like((np.cumsum(sorted_child_densities, axis=0)),
                             np.nan),
            where=(np.sum(sorted_child_densities, axis=0) != 0))

        # This section plots the number-density weighted ECDF for each child nuclide against the four error metrics

        plt.figure()
        for child_nuc_idx, child_nuc in enumerate(retained_child_nucs):

            plt.step(sorted_errors,
                     cumulative_child_density_fractions[:, child_nuc_idx],
                     where='post',
                     label=child_nuc)
        make_step_plots(
            f'{scoring_metric} Child Number-Density Weighted ECDF with Sample-Level Error',
            x_label_string,
            'Cumulative fraction of total child number density',
            f'{parent_nuc} {scoring_metric} Child Number Density-Weighted ECDF',
            f'{plot_folder}/{parent_nuc}_{scoring_metric}_all_children_weighted_ecdf.png',
            log_x=True,
            step_axes=None)

        # This section plots the number-density weighted ECDF for each child nuclide using the child-specific \
        # child-sum ratio for the x-axis. Only the child-sum ratio is plotted as the norm_abs_diff and norm_rel_diff \
        # would always be 0, and the cosine_similarity would always be 1.

        if scoring_metric == "child_sum_ratio":
            child_sum_ratios = calculate_per_child_child_sum_ratios(
                predicted_densities, true_densities, parent_nuc,
                retained_child_nucs)

            child_measure_error = make_plotting_errors(scoring_metric,
                                                       child_sum_ratios)

            child_ecdf_valid_mask = np.isfinite(child_measure_error)

            true_densities_p_removed = np.delete(
                true_densities, retained_child_nucs.index(parent_nuc), axis=1)

            child_retained_nucs = retained_child_nucs.copy()
            child_retained_nucs.pop(retained_child_nucs.index(parent_nuc))

            plt.figure()

            for child_nuc_idx, child_nuc in enumerate(child_retained_nucs):

                child_valid_mask = child_ecdf_valid_mask[:, child_nuc_idx]

                child_valid_errors = child_measure_error[child_valid_mask,
                                                         child_nuc_idx]
                child_valid_densities = true_densities_p_removed[
                    child_valid_mask, child_nuc_idx]

                child_sorted_indices = np.argsort(child_valid_errors)

                child_sorted_errors = child_valid_errors[child_sorted_indices]
                child_sorted_densities = child_valid_densities[
                    child_sorted_indices]

                child_cumulative_density_fractions = np.divide(
                    np.cumsum(child_sorted_densities),
                    np.sum(child_sorted_densities),
                    out=np.full_like(np.cumsum(child_sorted_densities),
                                     np.nan),
                    where=np.sum(child_sorted_densities) != 0)

                plt.step(child_sorted_errors,
                         child_cumulative_density_fractions,
                         where='post',
                         label=child_nuc)
            make_step_plots(
                f'{scoring_metric} Child Number-Density Weighted ECDF with Error Calculated Per Nuclide',
                x_label_string + ' Calculated Per Child',
                'Cumulative fraction of total number density per child',
                f'{parent_nuc} {scoring_metric} Child Number Density-Weighted ECDF Using Per-Child Error',
                f'{plot_folder}/{parent_nuc}_{scoring_metric}_all_children_weighted_ecdf_per_child_error.png',
                log_x=True,
                step_axes=None)


if __name__ == "__main__":
    main()
