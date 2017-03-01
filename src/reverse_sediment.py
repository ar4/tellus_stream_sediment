import argparse
import gdal, gdalnumeric, ogr, osr
from scipy.sparse import csr_matrix
from scipy.optimize import lsq_linear
import pandas as pd
import numpy as np
import os
import sys

#nodata_val = np.nan
#for colidx, cols in enumerate(colsArr):
#    sed = sed_all.loc[~sed_all[cols[0]].isnull()]
#    max_num_nonzero = fdir.size # an estimate, since don't know
#    num_rows = len(sed)
#    indices = np.zeros(max_num_nonzero,dtype=float)
#    indptr = np.zeros(num_rows+1,dtype=int)
#    Adata = np.ones(max_num_nonzero)
#    b = np.zeros(num_rows)
#    weight = np.zeros(fdir.shape, dtype=float)
#    nz_indices = 0
#
#    for Arow in range(num_rows):
#        indptr[Arow] = nz_indices
#        sourceCoords = sed.loc[sed.index[Arow], ['Easting', 'Northing']]
#        targetCoords = coordTrans.TransformPoint(float(sourceCoords[0]), float(sourceCoords[1]))
#        (col, row) = world2Pixel(geoTrans, targetCoords[0], targetCoords[1])
#        upstream = find_upstream(row, col)
#        for p in upstream:
#            pidx = p[0]*nx + p[1]
#            indices[nz_indices] = pidx
#            Adata[nz_indices] = 1.0/len(upstream)
#            weight[p] += 1.0/len(upstream)
#            nz_indices += 1
#    indptr[-1] = nz_indices
#    indices = indices[:nz_indices]
#    Adata = Adata[:nz_indices]
#    min_x_row = int(np.floor(np.min(indices) / nx))
#    max_x_row = int(np.ceil(np.max(indices) / nx))
#    num_x_rows = max_x_row - min_x_row + 1
#    indices -= min_x_row * nx
##    gdalnumeric.SaveArray(weight, '/scratch1/alan_r/weight_%d.tif' % colidx, prototype=dirs)
#    nodata_mask = (weight == 0.0)
#    Adata_bu = Adata.copy()
#    for col in cols:
#        b = sed[col].values
#        nan_idx = np.argwhere(np.isnan(b))
#        b[nan_idx] = 0.0
#        Adata[:] = Adata_bu[:]
#        for idx in nan_idx:
#            Adata[indptr[idx]:indptr[idx+1]] = 0.0
#        A = csr_matrix((Adata, indices, indptr), shape=(num_rows, nx*num_x_rows))
#        res = lsq_linear(A,b,bounds=(0.0, 10*np.max(b)),verbose=2,lsmr_tol='auto',max_iter=2)
#        x2 = res.x
#        x2 = x2.reshape([num_x_rows,nx])
#        x3 = np.zeros(fdir.shape)
#        x3[min_x_row:max_x_row+1,:] = x2
#        x3[nodata_mask] = nodata_val
#
#        gdalnumeric.SaveArray(np.float32(x3), '/scratch1/alan_r/border_ni_%s.tif' % col, prototype=dirs)

def load_data(column, measurements_file, upstream_file):
    measurements = pd.read_csv(measurements_file)[column].values
    upstream = np.load(upstream_file)
    return measurements, upstream

# dicts
#def find_nonzero_cells(valid_measurement_idxs, upstream):
#    pairs = {}
#    nonzero_idx = 0
#    for idx in valid_measurement_idxs:
#        for pair in upstream[idx]:
#            if pair not in pairs:
#                pairs[pair] = nonzero_idx
#                nonzero_idx += 1
#    return pairs
#
#def full_pair(reduced_idx, pairs):
#    return list(pairs.keys())[list(pairs.values()).index(reduced_idx)]

# list of pairs
#def find_nonzero_cells(valid_measurement_idxs, upstream):
#    pairs = []
#    for idx in valid_measurement_idxs:
#        for pair in upstream[idx]:
#            if pair not in pairs:
#                pairs.append(pair)
#    return pairs
#
#def reduced_idx(pair, pairs):
#    return pairs.index(reduced_idx)

# two lists
def find_min_max_nonzero_coords(valid_measurement_idxs, upstream):
    minx = 0
    maxx = np.inf
    miny = 0
    maxy = np.inf
    for idx in valid_measurement_idxs:
        for pair in upstream[idx]:
            if pair[1] < minx:
                minx = pair[1]
            if pair[1] > maxx:
                maxx = pair[1]
            if pair[0] < miny:
                miny = pair[0]
            if pair[0] > maxy:
                maxy = pair[0]
    return minx, maxx, miny, maxy

def find_nonzero_cells(valid_measurement_idxs, upstream):
    minx, maxx, miny, maxy = find_min_max_nonzero_coords(valid_measurement_idxs, upstream)
    full_pairs = []
    reduced_idxs = np.zeros([maxy - miny + 1, maxx - minx + 1], dtype=int)
    nonzero_idx = 0
    for idx in valid_measurement_idxs:
        for pair in upstream[idx]:
            if pair not in full_pairs:
                full_pairs.append(pair)
                reduced_idxs[pairs[0] - miny, pairs[1] - minx] = nonzero_idx
                nonzero_idx += 1
    return full_pairs, reduced_idxs

def run(output, column, measurements_file, upstream_file):
    measurements, upstream = load_data(column, measurements_file, upstream_file)
    valid_measurement_idxs = np.argwhere(np.isfinite(measurements))
    num_rows = len(valid_measurement_idxs)
    full_pairs, reduced_idxs = find_nonzero_cells(valid_measurement_idxs, upstream)
    num_nonzero = len(full_pairs)

    A = build_A(upstream, reduced_idxs, num_nonzero)
    b = measurements[valid_measurement_idxs]

    solve(A, b, full_pairs
            # need to convert pixels to coords so can write tiff:
            # need origin, pixel sizes, projection used in upstream

    indices = np.zeros(max_num_nonzero,dtype=float)
    indptr = np.zeros(num_rows+1,dtype=int)
    Adata = np.ones(max_num_nonzero)
    b = np.zeros(num_rows)
    weight = np.zeros(fdir.shape, dtype=float)
    nz_indices = 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, help="path to output file", required=True)
    parser.add_argument("--column", type=str, help="name of column in CSV file to process", required=True)
    parser.add_argument("--measurements", type=str, help="path to measurements csv file", required=True)
    parser.add_argument("--upstream", type=str, help="path to upstream npy file", required=True)
    args = parser.parse_args()
    run(args.output, args.column, args.measurements, args.upstream)
