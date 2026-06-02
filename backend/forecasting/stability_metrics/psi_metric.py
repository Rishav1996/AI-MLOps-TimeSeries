"""Population Stability Index (PSI): distribution-drift between two samples."""
import numpy as np


def metric_loss(expected, actual, bucket_type='bins', buckets=10, axis=0):
    """Return the PSI between expected and actual arrays (higher = more drift)."""
    expected = np.array(expected).flatten()
    actual = np.array(actual).flatten()

    def psi(expected_array, actual_array, no_of_buckets):
        """Compute PSI for a single pair of 1-D arrays over no_of_buckets bins."""
        def scale_range(input, min, max):
            """Linearly rescale input array to the [min, max] range."""
            input += -(np.min(input))
            input /= np.max(input) / (max - min)
            input += min
            return input

        breakpoints = np.arange(0, no_of_buckets + 1) / no_of_buckets * 100

        if bucket_type == 'bins':
            breakpoints = scale_range(breakpoints, np.min(expected_array), np.max(expected_array))
        elif bucket_type == 'quantiles':
            breakpoints = np.stack([np.percentile(expected_array, b) for b in breakpoints])

        expected_percents = np.histogram(expected_array, breakpoints)[0] / len(expected_array)
        actual_percents = np.histogram(actual_array, breakpoints)[0] / len(actual_array)

        def sub_psi(e_perc, a_perc):
            """PSI contribution for a single bucket; clamps zero percents to 0.0001."""
            if a_perc == 0:
                a_perc = 0.0001
            if e_perc == 0:
                e_perc = 0.0001

            value = (e_perc - a_perc) * np.log(e_perc / a_perc)
            return value

        psi_value = np.sum([sub_psi(expected_percents[i], actual_percents[i]) for i in range(0, len(expected_percents))])

        return psi_value

    if len(expected.shape) == 1:
        psi_values = np.empty(len(expected.shape))
    else:
        psi_values = np.empty(expected.shape[axis])

    for i in range(0, len(psi_values)):
        if len(psi_values) == 1:
            psi_values = psi(expected, actual, buckets)
        elif axis == 0:
            psi_values[i] = psi(expected[:,i], actual[:,i], buckets)
        elif axis == 1:
            psi_values[i] = psi(expected[i,:], actual[i,:], buckets)

    return psi_values
