"""Estimate the substance concentration in cells that are upstream from measurements.
"""
import argparse
import gdal
from scipy.sparse import csr_matrix
from scipy.optimize import lsq_linear
import pandas as pd
import numpy as np

def load_data(column, measurements_file, upstream_file, flow_directions_file):
    """Load the input datasets, and extract the part that is relevant for the current substance.
    """
    measurements = pd.read_csv(measurements_file)[column].values
    upstream = np.load(upstream_file)
    flow_directions = gdal.Open(flow_directions_file)

    valid_measurement_idxs = np.isfinite(measurements)

    measurements = measurements[valid_measurement_idxs]
    upstream = upstream[valid_measurement_idxs]
    return measurements, upstream, flow_directions

# two lists
def find_min_max_nonzero_coords(upstream):
    """Find the min and max of the x and y coordinates in upstream.
    """
    minx = np.inf
    maxx = -np.inf
    miny = np.inf
    maxy = -np.inf
    for _, upstream_coords in enumerate(upstream):
        for coord in upstream_coords:
            if coord[1] < minx:
                minx = coord[1]
            if coord[1] > maxx:
                maxx = coord[1]
            if coord[0] < miny:
                miny = coord[0]
            if coord[0] > maxy:
                maxy = coord[0]
    return minx, maxx, miny, maxy

def find_nonzero_cells(upstream):
    """Reduce the system to the cells that we will solve for.
       Construct arrays to allow conversion between full and these reduced coordinates.
       Also return the number of nonzero entries that there will be in the
       A matrix so that this memory can be allocated in build_A.
    """
    minx, maxx, miny, maxy = find_min_max_nonzero_coords(upstream)
    nx = maxx - minx + 1
    ny = maxy - miny + 1
    if not np.isfinite(nx):
        nx = 0
    if not np.isfinite(ny):
        ny = 0
    # coordinate pairs of points in full 2D landscape that will be solved for
    full_coords = []
    # a 2D landscape with cells that will be solved for containing their
    # index in the reduced-size system that will be solved
    # initialize to -1 to indicate that value has not been set
    reduced_idxs = -1*np.ones([ny, nx], dtype=np.int)
    reduced_idx = 0
    num_nonzero = 0
    for coords_upstream_of_measurement in upstream:
        for coord in coords_upstream_of_measurement:
            if reduced_idxs[coord[0] - miny, coord[1] - minx] < 0:
                # point has not been added to the reduced system yet, so add it
                full_coords.append(coord)
                reduced_idxs[coord[0] - miny, coord[1] - minx] = reduced_idx
                reduced_idx += 1
            num_nonzero += 1
    return full_coords, reduced_idxs, num_nonzero, minx, miny

def build_A(upstream, full_coords, reduced_idxs, num_nonzero, minx, miny):
    """Form the A matrix that will be used to solve for substance concentration.
       This is the A matrix in the Ax=b system of equations, where x is a
       column vector of the substance concentration to be solved for, and b is a
       column vector of the measurements.
       A is a sparse matrix to save memory.
    """
    num_rows = len(upstream)
    indices = np.zeros(num_nonzero, dtype=np.int)
    indptr = np.zeros(num_rows+1, dtype=np.int)
    Adata = np.ones(num_nonzero, dtype=np.float32)

    nz_idx = 0
    for row_idx in range(num_rows):
        indptr[row_idx] = nz_idx
        for coord in upstream[row_idx]:
            reduced_idx = reduced_idxs[coord[0] - miny, coord[1] - minx]
            indices[nz_idx] = reduced_idx
            Adata[nz_idx] = 1.0/len(upstream[row_idx])
            nz_idx += 1
    assert(nz_idx == num_nonzero)
    indptr[-1] = nz_idx
    A = csr_matrix((Adata, indices, indptr), shape=(num_rows, len(full_coords)))

    return A

def solve(A, b, full_coords, flow_directions, max_iter=4):
    """Solve for the substance concentration.
       The lsq_linear solver is used so that a lower bound of 0 can be set on the
       output (negative substance concentration is not allowed).
       The flow_directions file, which was used to generate the coordinates in upstream,
       is used to find the size of the 2D output, allowing the results to be
       converted from reduced coordinates to the full 2D array.
    """
    if len(b) > 0:
        res = lsq_linear(A, b, bounds=(0.0, np.inf), verbose=2, lsmr_tol='auto', max_iter=max_iter)
        res = res.x
    else:
        res = []
    nx = flow_directions.RasterXSize
    ny = flow_directions.RasterYSize
    x = np.nan * np.ones([ny, nx], dtype=np.float32)
    for reduced_idx, value in enumerate(res):
        full_coord = full_coords[reduced_idx]
        x[full_coord[0], full_coord[1]] = value
    return x

def write_output(x, output_file, flow_directions):
    """Write the output substance concentration map to the specified file in GeoTiff format.
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
    full_coords, reduced_idxs, num_nonzero, minx, miny = find_nonzero_cells(upstream)

    A = build_A(upstream, full_coords, reduced_idxs, num_nonzero, minx, miny)
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
