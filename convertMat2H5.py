#!/usr/bin/env python3
#
# Routine for converting a (old) Matlab file to an HDF5 file.
# Requires DREAM.
#

import h5py
import numpy as np
from numpy.dtypes import VoidDType
from scipy.io import loadmat
from DREAM import DREAMIO


def mat2dict(filename):
    """
    Convert the contents of the specified MAT file to a Python dictionary.
    """
    A = loadmat(filename)
    d = {}
    for k in A.keys():
        if type(A[k]) == np.ndarray:
            d[k] = extractArray(A[k], path=k)
        elif type(A[k]) == bytes:
            d[k] = A[k].decode('utf-8')
        elif type(A[k]) == str:
            d[k] = A[k]
        elif type(A[k]) == list:
            # Ignore (not sure how to convert this...)
            pass

    return d


def extractArray(arr, path):
    """
    Extract a numpy array from the given MAT struct.
    """
    if len(arr.dtype) >= 1:
        if arr.size != 1:
            print(f"WARNING: Cannot convert structure of arrays to HDF5: '{path}'.")
            return None

        d = {}
        for k in arr.dtype.names:
            d[k] = extractArray(arr[0,0][k], path=path+f'/{k}')
        return d
    elif arr.dtype == 'O':
        a = np.zeros((arr.size, arr[0,0].size))
        for i in range(arr.size):
            a[i,:] = arr[0,i][0,:]

        return a
    else:
        return arr


def convert(filename, h5file):
    """
    Convert the Matlab file 'filename' to an HDF5 file. The argument
    'h5file' can be either an HDF5 file handle or a string, indicating
    the HDF5 file should be created with the specified name.
    """
    if type(h5file) == str:
        f = h5py.File(h5file, 'w')
    else:
        f = h5file

    d = mat2dict(filename)
    DREAMIO.dict2h5(f, d)


