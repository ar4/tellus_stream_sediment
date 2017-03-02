#!/usr/bin/env python
"""Find the upstream cells for each row in the input CSV.
"""

import sys
import os
import argparse
import gdal, gdalnumeric, ogr, osr
import pandas as pd
import numpy as np

# 10000 is an arbitrary number and may need to be increased
sys.setrecursionlimit(10000)

# Necessary for my version of GDAL to avoid errors such as
# ERROR 4: Unable to open EPSG support file gcs.csv
os.environ['GDAL_DATA'] = os.popen('gdal-config --datadir').read().rstrip()

# The coordinates of the neighbour to which flow is directed
# e.g. if the flow direction value is 1, dx=1, dy=0, so flow is
# to the neighbour to the west, whereas if the value is 3, flow
# is to the south (0, 1)
dx=[0,1,1,0,-1,-1,-1,0,1]
dy=[0,0,1,1,1,0,-1,-1,-1]

def find_upstream(flow_directions, row, col):
    """Recursively find the coordinate pairs of upstream points
    """
    # 32 64 128
    # 16 0  1
    # 8  4  2
    upstream = [(row, col)]
    for k in range(1,9):
        if (0 <= row+dy[k] < flow_directions.shape[0]) and (0 <= col+dx[k] < flow_directions.shape[1]):
            nv = flow_directions[row+dy[k], col+dx[k]]
            if nv == 0:
                ni = 0
            else:
                ni = int(np.log2(nv))+1
            if (dx[ni] == -dx[k]) & (dy[ni] == -dy[k]):
                upstream = upstream + find_upstream(flow_directions, row+dy[k], col+dx[k])
    return upstream

def world2Pixel(geoMatrix, x, y):
    """Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate
    the pixel location of a geospatial coordinate
    """
    ulX = geoMatrix[0]
    ulY = geoMatrix[3]
    xDist = geoMatrix[1]
    yDist = geoMatrix[5]
    rtnX = geoMatrix[2]
    rtnY = geoMatrix[4]
    pixel = int((x - ulX) / xDist)
    line = int((ulY - y) / xDist)
    return (pixel, line)

def process_row(row, flow_directions, coordTrans, geoTrans):
    """Find the upstream points for one row of the input CSV
    """
    sourceCoords = row[['Easting', 'Northing']]
    targetCoords = coordTrans.TransformPoint(float(sourceCoords[0]), float(sourceCoords[1]))
    (col, row) = world2Pixel(geoTrans, targetCoords[0], targetCoords[1])
    upstream = find_upstream(flow_directions, row, col)
    return upstream

def load_inputs(input_csv, csv_epsg, flow_directions_file):
    """Load input files and reproject CSV to same projection and flow directions
    """
    raster = gdal.Open(flow_directions_file)
    flow_directions = gdalnumeric.LoadFile(flow_directions_file)
    input_df = pd.read_csv(input_csv)

    # Reproject vector geometry to same projection as raster
    sourceSR = osr.SpatialReference()
    sourceSR.ImportFromEPSG(csv_epsg)
    targetSR = osr.SpatialReference()
    targetSR.ImportFromWkt(raster.GetProjectionRef())
    coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
    geoTrans = raster.GetGeoTransform()

    return (input_df, flow_directions, coordTrans, geoTrans)

def run(output_file, input_csv, csv_epsg, flow_directions_file):
    """Main driver function.
    """

    (input_df, flow_directions, coordTrans, geoTrans) = load_inputs(input_csv, csv_epsg, flow_directions_file)

    upstream = []
    for index, row in input_df.iterrows():
        upstream.append(process_row(row, flow_directions, coordTrans, geoTrans))
    np.save(output_file, upstream)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, help="path to output upstream npy file", required=True)
    parser.add_argument("--measurements", type=str, help="path to measurements csv file", required=True)
    parser.add_argument("--measurements_epsg", type=int, help="EPSG of measurements csv file spatial reference", required=True)
    parser.add_argument("--flow_directions", type=str, help="path to flow directions file", required=True)
    args = parser.parse_args()
    run(args.output, args.measurements, args.measurements_epsg, args.flow_directions)
