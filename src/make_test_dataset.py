import os
import argparse
import gdal, osr
import numpy as np
import pandas as pd

# Necessary for my version of GDAL to avoid errors such as
# ERROR 4: Unable to open EPSG support file gcs.csv
os.environ['GDAL_DATA'] = os.popen('gdal-config --datadir').read().rstrip()

N=5

def create_test_flow_directions(output_path):
    flow_directions = 4*np.ones([N, 1], dtype=np.uint8)
    flow_directions[-1,0] = 0

    driver = gdal.GetDriverByName('GTiff')

    dataset = driver.Create(output_path, 1, N, 1, gdal.GDT_Byte)

    dataset.SetGeoTransform((
        -10.601476282215518,
        0.000833385971806,
        0,
        55.571185968814824,
        0,
        -0.000833397668502))  
    proj = osr.SpatialReference()
    proj.ImportFromEPSG(4326)
    dataset.SetProjection(proj.ExportToWkt())
    dataset.GetRasterBand(1).WriteArray(flow_directions)
    dataset = None

def create_test_measurements(output_path):
    easting = (-10.601476282215518 + 0.5*0.000833385971806)*np.ones(2)
    northing = np.zeros(2)
    northing[0] = 55.571185968814824 - (0.5+1)*0.000833397668502
    northing[1] = 55.571185968814824 - (0.5+3)*0.000833397668502
    # Reproject vector geometry from WGS84 to Irish National Grid
    #'EPSG:29901, OSNI 1952 / Irish National Grid'
    sourceSR = osr.SpatialReference()
    sourceSR.ImportFromEPSG(4326)
    targetSR = osr.SpatialReference()
    targetSR.ImportFromEPSG(29901)
    coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
    for i in range(len(easting)):
        new_coords = coordTrans.TransformPoint(float(easting[i]), float(northing[i]))
        easting[i] = new_coords[0]
        northing[i] = new_coords[1]
    na = [1.0, 1.0]
    mg = [0.0, 0.5]
    al = [1.0, 0.5]
    si = [np.nan, 1.0]
    p2 = [0.0, 0.0]
    s = [np.nan, np.nan]
    dataset = pd.DataFrame({'Easting':easting, 'Northing':northing, 'Na2O_%':na, 'MgO_%':mg, 'Al2O3_%': al, 'SiO2_%': si, 'P2O5_%': p2, 'S_mgkg': s})
    dataset.to_csv(output_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurements", type=str, help="path to measurements csv file")
    parser.add_argument("--flow_directions", type=str, help="path to flow directions file")
    args = parser.parse_args()
    if (args.measurements):
        create_test_measurements(args.measurements)
    if (args.flow_directions):
        create_test_flow_directions(args.flow_directions)
