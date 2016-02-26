from celery import Celery
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from mltsp.cfg import config
from mltsp import time_series
from mltsp import util
from mltsp import featurize_tools as ft


celery_app = Celery('celery_fit', broker=config['celery']['celery_broker'])
celery_app.config_from_object(config['celery'])


@celery_app.task(name="celery_tasks.check_celery")
def check_celery():
    """Test task."""
    return "OK"


def celery_available():
    """Test Celery task; this is much faster than running `celery status`."""
    try:
        res = check_celery.apply_async()
        return "OK" == res.get(timeout=2)
    except:
        return False


@celery_app.task(name="celery_tasks.featurize_ts_file")
def featurize_ts_file(ts_file_path, features_to_use, custom_script_path=None):
    """Featurize time-series data file.

    Parameters
    ----------
    ts_file_path : str
        Time-series data file disk location path.
    features_to_use : list of str
        List of names of features to be generated.
    custom_script_path : str, optional
        Path to custom features script .py file, if applicable.

    Returns
    -------
    tuple
        Two-element tuple whose first element is the file name and
        second element is a dictionary of features.

    """
    short_fname = util.shorten_fname(ts_file_path)
    ts = time_series.from_netcdf(ts_file_path)
    all_features = ft.featurize_single_ts(ts, features_to_use,
                                          custom_script_path)
    return (short_fname, all_features, ts.target, ts.meta_features)


@celery_app.task(name="celery_tasks.featurize_ts_data")
def featurize_ts_data(time_series, features_to_use, custom_script_path=None,
                      custom_functions=None):
    """Featurize time-series objects.

    Parameters
    ----------
    time_series : TimeSeries object
        Time series data to be featurized.
    custom_script_path : str, optional
        Path to custom features script .py file, if applicable.
    custom_functions : dict, optional
        Dictionary of custom feature functions to be evaluated for the given
        time series, or a dictionary representing a dask graph of function
        evaluations. Dictionaries of functions should have keys `feature_name`
        and values functions that take arguments (t, m, e); in the case of a
        dask graph, these arrays should be referenced as 't', 'm', 'e',
        respectively, and any values with keys present in `features_to_use`
        will be computed.

    Returns
    -------
    tuple
        Two-element tuple whose first element is the time series name and
        second element is a dictionary of features.

    """
    all_features = ft.featurize_single_ts(time_series, features_to_use,
                                          custom_script_path, custom_functions)
    return (time_series.name, all_features)
