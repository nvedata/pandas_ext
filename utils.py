from collections import defaultdict
import datetime
import hashlib

import numpy as np
import pandas as pd

def excel_date(date):
    '''
    Converting date to Excel date or from Excel date
    
    Parameters
    ----------
    date : float, int OR str, datetime.datetime, pd.Timestamp
    Excel date as float/int OR date recognized by pandas. 
    
    Returns
    ----------
    date : float, int OR pd.Timestamp
    Excel date as float/int or date as pd.Timestamp.
    '''
    
    #unlike python, 29.02.1900 exists in excel
    #since 01.03.2019 pandas and excel calendar has equal dates
    cons_date = pd.Timestamp(year=1900, month=3, day=1)
    excel_cons_date = 61
    
    if isinstance(date, (str, datetime.datetime, pd.Timestamp)):
        return (pd.to_datetime(date) - cons_date).days + excel_cons_date
    
    elif isinstance(date, (np.int, np.float)):
        return cons_date + pd.Timedelta(days=date - excel_cons_date)
        
    else:
        raise TypeError('expected str, datetime, float, int, got ', type(date))

def time_derivative(series, time_unit=pd.Timedelta('1s')):
    '''
    Calculate time derivative from right for each point in series. Ignores NaN.
    
    Parameters
    ---------
    series: pd.Series with numeric data with pd.DatetimeIndex
    time_unit: pd.Timedelta
    
    Returns
    ---------
    dsdt : pd.Series
    '''
    
    ds=series.dropna().diff()
    dt=ds.index.to_series().diff()
    dsdt=ds/(dt/time_unit)
    return dsdt

def isnumber(a):
    '''Check if string can be converted fo float'''
    try:
        float(a)
        return True
    except:
        return False
    
def convert_cyr_month(series):
    '''Convert cyrillic name of month in series to month number (i.e. 01, 02, ..., 12)
    Parameters
    ----------
    series: pd.Series of str
    
    Returns
    ----------
    series: pd.Series
    '''
    series=series.copy()
    
    repl_dict={
    'янв\\w*' : '01',    
    'фев\\w*' : '02',    
    'мар\\w*' : '03',
    'апр\\w*' : '04',
    'май\\w*' : '05',
    'июн\\w*' : '06',
    'июл\\w*' : '07',
    'авг\\w*' : '08',
    'сен\\w*' : '09',
    'окт\\w*' : '10',
    'ноя\\w*' : '11',
    'дек\\w*' : '12'
    }
    
    for k, v in repl_dict.items():
        series=series.str.replace(k, v)
    
    return series

def read_all_sheets(add_sheet_name=True, **kwargs):
    '''Read all sheets from Excel file
    Parameters
    ----------
    add_sheet_name: bool
    Add to dataframe column with sheet name for each sheet
    pd.ExcelFile **kwargs
    
    Returns
    ----------
    sheets: list of pd.DataFrame
    '''
    book=pd.ExcelFile(**kwargs)
    
    sheets=[]
    for sh in book.sheet_names:
        sheet=book.parse(sh)
        sheet['sheet_name']=sh
        sheets.append(sheet)

    return sheets

def timeseries_info(df):
    
    '''Timeseries start, end and frequency.
    
    Parameters
    ----------
    df: pd.DataFrame or pd.Series with pd.DatetimeIndex
    
    Returns
    ----------
    start: pd.Timestamp
    end: pd.Timestamp
    freq: pd.Series
    '''
    
    start = df.index.min()
    end = df.index.max()
    freq = df.index.to_series().diff().value_counts()
    return start, end, freq

def bool_report(series):
    '''Returns groups of indices for bool series provided from dataframe tests.
    Parameters
    ----------
    series: pd.Series of bool
    
    Returns
    ----------
    report: dict
    '''
    return series.groupby(series).groups

def floating_filter(df, value):
    '''Find single row of dataframe by value in any column.
    df: pd.DataFrame
    value: scalar'''
    #TODO array instead value: single run with 3d approach
    #TODO merge behavior: several matching rows
    
    val_mask=(df.values==value)
    if (val_mask.sum(axis=0)>1).any():
        raise ValueError('non-unique value %s in matching dataframe' % value)
    if (val_mask.sum(axis=0)==0).all():
        return pd.Series(name=value)
        
    series=df[val_mask.any(axis=1)].iloc[0].copy()
    series.name=value
    return series

def get_related_df(matching, values, related_columns):
    '''Return list of values from related columns if any given
    values contains in row of matching.
    
    Parameters
    ----------
    matching : pd.DataFrame
    
    values : 1d list-like
    Values to search in rows of matching.
    
    related_columns : 1d list-like
    Columns of matching.
    
    Returns
    -------
    related_df : pd.DataFrame
    DataFrame with passed values as index.
    '''

    val_arr = np.array(values)
    mask = flow_matching.values[:, :, np.newaxis] == val_arr
    row_mask = mask.any(axis=1)
    m_idx, val_idx = np.nonzero(row_mask)
    related_df = matching[related_columns].iloc[m_idx]
    related_df.index = val_arr[val_idx]
    return  related_df

def columnwise_rolling(df, windows, aggfunc, **kwargs):
    '''Rolling dataframe aggregation with individual window for each column.
    Parameters
    ----------
    df : pd.DataFrame
    windows: pd.Series of int
    Rolling window periods for each column.
    aggfunc: str or callable
    **kwargs : rolling method kwargs
    
    Returns
    -------
    df : pd.DataFrame
    '''
    return df.apply(lambda x: x\
                    .rolling(windows[x.name], **kwargs)\
                    .agg(aggfunc))

def columnwise_shift(df, offsets, freq):
    '''Shift each column with individual offset.
    Parameters
    ----------
    df : pd.DataFrame
    offsets : pd.Series of int
    Offsets for each column.
    aggfunc : str or callable
    **kwargs : shift kwargs
    
    Returns
    -------
    df : pd.DataFrame
    '''
    return df.apply(lambda x: x\
                    .shift(-offsets[x.name], freq=freq))

def recursive_set(list_like):
    '''Returns set of scalar elements of list-like.
    Strings and types without __len__() method are considered as scalars.
    Can be used as aggregation function.'''
    
    scalars = set()
    for i in list_like:
        #scalar check
        if hasattr(i, '__len__') and not isinstance(i, str):
            scalars = scalars.union(recursive_set(i))
        else:
            scalars.add(i)
            
    return scalars

def recursive_flatten(list_like):
    '''Returns list of scalar elements of list-like.
    Strings and types without __len__() method are considered as scalars.'''
    
    scalars = []
    for i in list_like:
        #scalar check
        if hasattr(i, '__len__') and not isinstance(i, str):
            scalars += recursive_flatten(i)
        else:
            scalars.append(i)
            
    return scalars


def hash_df(df, hashfunc=hashlib.sha1):
    '''Get hex hash of dataframe values.
    
    Parameters
    ----------
    df : pd.DataFrame
    hashfunc : callable, default hashlib.sha1
    Hash function from hashlib package.
    
    Returns
    -------
    hash: str
    '''
    return hashfunc(df.values.tobytes()).hexdigest()

def regroup_dict(d):
    '''Regroup dictionary when values are sets
    by elements of these sets.
    
    Parameters
    ----------
    d : dict when values are sets.
    
    Returns
    -------
    re_d : dict when values are sets.
    '''
    
    re_d = defaultdict(set)
    for k, v in d.items():
        for i in v:
            re_d[i].add(k)
    
    return re_d

def subseries_count(a):
    '''
    Count subseries of True in array.
    
    Parameters
    ----------
    a : 1d np.ndarray, dtype=bool
    
    Returns
    -------
    subs_start_idx : 1d np.ndarray
    Indices of subseries start.
    
    count : 1d np.ndarray
    '''
    marked_a = np.cumsum(~a)
    labels, count = np.unique(marked_a, return_counts=True)
    mask = count > 1
    subs_start_idx = np.searchsorted(marked_a, labels[mask]) + 1
    return subs_start_idx, count[mask] - 1

def nondecr_subarray_len(arr):
    '''Return length of non-decreasing subarrays of given array.
    Parameters
    ----------
    arr : 1d np.ndarray
    
    Returns
    -------
    subarr_len : 1d np.ndarray'''
    
    with np.errstate(invalid='ignore'):
        decr_mask = arr[:-1] > arr[1:]
    idx = np.arange(1, arr.shape[0])
    neg_diff_idx = idx[decr_mask]
    subarr_len = np.diff(neg_diff_idx, prepend=0, append=arr.shape[0])
    
    return subarr_len

def value_subarray_len(arr, value):
    '''Find length of consecutive subseries of value in array.
    Parameters
    ----------
    arr : 1d array-like
    value : hashable value
    
    Returns
    -------
    subarrays : dict
    Keys are indices of first elements of consecutive series of value.
    Values are length of consecutive series of value.
    '''
    subarrays=defaultdict(int)
    prev_val = np.nan
    for i, val in enumerate(arr):
        if val == value:
            if val != prev_val:
                substart = i

            subarrays[substart] += 1
        prev_val = val
            
    return dict(subarrays)

def const_check(arr, ignore_nan=True):
    '''Check if all values in array are equal.
    
    Parameters
    ----------
    arr : 1d np.ndarray
    ignore_nan : bool
    
    Returns
    -------
    output : bool
    '''

    if ignore_nan:
        na_mask = np.isnan(arr)
        return (arr[~na_mask] == arr[~na_mask][0]).all()
    else:
        return (arr == arr[0]).all()

def make_output(flagged_outputs):
    '''Return objects according it's flags.
    
    Parameters
    ----------
    flagged_outputs : list of tuples (object, bool)
    
    Returns
    -------
    output : list or None
    '''
    output = [out for out, flag in flagged_outputs if flag]
    return output

def inverse_agg_count(series):
    '''
    Inverse count agregation.
    
    Parameters
    ----------
    series : pd.Series with 1d index
    Count aggregation result.
    
    Returns
    -------
    index : 1d index
    Index values repeated series.values times.
    index.to_series().groupby(index).count() returns series.
    '''
    return np.repeat(series.index, series)

def repeat_range(repeats, range_step=1):
    '''
    Repeat range.
    
    Parameters
    ----------
    repeats : 1d np.ndarray, dtype=int
    Nonzero number of repetitions for each element in range.
    
    range_step : int
    Step of sequence of integers from 0 to len(repeats).
    
    Returns
    -------
    res : 1d np.ndarray, dtype : int
    '''
    idx = repeats.cumsum()
    res = np.zeros(idx[-1], dtype=int)
    res[idx[:-1]] = range_step
    res = res.cumsum()
    return res

def equal_multiple(*arrays):
    '''
    Compare multiple arrays.
    
    Parameters
    ----------
    arrays : tuple of 1d np.ndarray
    
    Returns
    -------
    bool
    '''
    return np.all(np.vstack(arrays) == arrays[0])

def safe_getitem(iterable, key, default):
    '''
    Get item from iterable by key or index.
    Return default value when key or index is unavailable.
    
    Parameters
    ----------
    iterable : iterable
    
    key : hashable
    Iterable index or key.
    
    default : object
    
    Returns
    -------
    object
    '''
    try:
        return iterable[key]
    except (IndexError, KeyError):
        return default

def flatten_multiindex(index, sep='_'):
    '''
    Flatten multiindex with joined column names.
    
    Parameters
    ----------
    index : pd.MultiIndex
    
    sep : str
    
    Returns
    -------
    pd.Index
    '''
    return index.to_flat_index().str.join(sep)
