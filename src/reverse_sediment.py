import argparse
import gdal, gdalnumeric, ogr, osr
from scipy.sparse import csr_matrix
from scipy.optimize import lsq_linear
import pandas as pd
import numpy as np
import os
import sys

def load_data(column, measurements_file, upstream_file, flow_directions_file):
    """Load the input datasets, and extract the part that is relevant for the current substance.
    """
    measurements = pd.read_csv(measurements_file)[column].values
    upstream = np.load(upstream_file)
    flow_directions = gdal.Open(flow_directions_file)

    valid_measurement_idxs = np.argwhere(np.isfinite(measurements))

    measurements = measurements[valid_measurement_idxs]
    upstream = upstream[valid_measurement_idxs]
    return measurements, upstream, flow_directions

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
    """Find the min and max of the x and y coordinates in upstream.
    """
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

def find_nonzero_cells(upstream):
    """Reduce the system to the cells that we will solve for.
       Construct arrays to allow conversion between full and these reduced coordinates.
       Also return the number of nonzero entries that there will be in the
       A matrix so that this memory can be allocated in build_A.
    """
       
    minx, maxx, miny, maxy = find_min_max_nonzero_coords(upstream)
    # coordinate pairs of points in full 2D landscape that will be solved for
    full_coords = []
    # a 2D landscape with cells that will be solved for containing their
    # index in the reduced-size system that will be solved
    # initialize to -1 to indicate that value has not been set
    reduced_idxs = -1*np.ones([maxy - miny + 1, maxx - minx + 1], dtype=np.int)
    reduced_idx = 0
    num_nonzero = 0
    for coords_upstream_of_measurement in upstream:
        for coord in coords_upstream_of_measurement:
            if reduced_idxs[coord[0] - miny, coord[1] - minx] < 0:
                # point has not been added to the reduced system yet, so add it
                full_coords.append(pair)
                reduced_idxs[coord[0] - miny, coord[1] - minx] = reduced_idx
                reduced_idx += 1
            num_nonzero += 1
    return full_coords, reduced_idxs, num_nonzero

def build_A(upstream, reduced_idxs, num_nonzero):
    """Form the A matrix that will be used to solve for substance abundance.
       This is the A matrix in the Ax=b system of equations, where x is a
       column vector of the substance abundance to be solved for, and b is a
       column vector of the measurements.
       A is a sparse matrix to save memory.
    """
    num_rows = len(upstream)
    indices = np.zeros(num_nonzero,dtype=np.int)
    indptr = np.zeros(num_rows+1,dtype=np.int)
    Adata = np.ones(num_nonzero,dtype=np.float32)

    nz_idx = 0
    for row_idx in range(num_rows):
        indptr[row_idx] = nz_idx
        for coord in upstream[row_idx]:
            reduced_idx = reduced_idxs[coord[0], coord[1]]
            indices[nz_idx] = reduced_idx
            Adata[nz_idx] = 1.0/len(upstream_coords)
            nz_idx += 1
    assert(nz_idx == num_nonzero)
    indptr[-1] = nz_idx
    A = csr_matrix((Adata, indices, indptr), shape=(num_rows, len(reduced_idxs)))

    return A

def solve(A, b, full_coords, max_iter=2, flow_directions):
    """Solve for the substance abundance.
       The lsq_linear solver is used so that a lower bound of 0 can be set on the
       output (negative substance abundance is not allowed).
       The flow_directions file, which was used to generate the coordinates in upstream,
       is used to find the size of the 2D output, allowing the results to be
       converted from reduced coordinates to the full 2D array.
    """
    res = lsq_linear(A, b, bounds=(0.0, np.inf), verbose=2, lsmr_tol='auto', max_iter=max_iter)
    nx = flow_directions.RasterXSize
    ny = flow_directions.RasterYSize
    x = np.nan * np.ones([ny, nx],dtype=np.float32)
    for reduced_idx, value in enumerate(res.x):
        full_coord = full_coords[reduced_idx]
        x[full_coord[0], full_coord[1]] = value
    return x

def write_output(x, output_file, flow_directions):
    """Write the output substance abundance map to the specified file in GeoTiff format.
       The flow_directions file is used as a prototype for the output file, with the
       differences being a different datatype and NoData value.
    """
    driver = gdal.GetDriverByName('GTiff')
    nx = flow_directions.RasterXSize
    ny = flow_directions.RasterYSize
    dataset = driver.Create(output_file, nx, ny, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform(flow_directions.GetGeoTransform())
    dataset.SetProjection(flow_directions.GetProjection())
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(np.nan)
    band.WriteArray(x)
    dataset = None

def run(output_file, column, measurements_file, upstream_file, flow_directions_file):
    """Main driver.
    """
    measurements, upstream, flow_directions = load_data(column, measurements_file, upstream_file, flow_directions_file)
    full_coords, reduced_idxs, num_nonzero = find_nonzero_cells(upstream)

    A = build_A(upstream, reduced_idxs, num_nonzero)
    b = measurements

    x = solve(A, b, full_coords, flow_directions)
    write_output(x, output_file, flow_directions)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, help="path to output file", required=True)
    parser.add_argument("--column", type=str, help="name of column in CSV file to process", required=True)
    parser.add_argument("--measurements", type=str, help="path to measurements csv file", required=True)
    parser.add_argument("--upstream", type=str, help="path to upstream npy file", required=True)
    parser.add_argument("--flow_directions", type=str, help="path to flow directions file", required=True)
    args = parser.parse_args()
    run(args.output, args.column, args.measurements, args.upstream, args.flow_directions)
