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
    Can be used as aggregation function.'''
    
    scalars = set()
    for i in list_like:
        #scalar check
        if hasattr(i, '__setitem__'):
            scalars = scalars.union(recursive_set(i))
        else:
            scalars.add(i)
            
    return scalars

def recursive_flatten(list_like):
    '''Returns list of scalar elements of list-like'''
    
    scalars=[]
    for i in list_like:
        #scalar check
        if hasattr(i, '__setitem__'):
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
