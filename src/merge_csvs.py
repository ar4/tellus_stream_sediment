#!/usr/bin/env python
"""Join stream sediment data from different Tellus surveys
into a single CSV file to ease later processing.
"""

import os
import pandas as pd

def fix_northern_ireland(northern_ireland_data):
    """Modify Northern Ireland columns to match Border ones.
    """

    northern_ireland_data.drop(['YEAR', 'LABNO'], axis=1, inplace=True)
    northern_ireland_data.columns = ['Sample_ID', 'Easting', 'Northing', 'MgO_%',
                                     'P2O5_%', 'K2O_%', 'CaO_%', 'MnO_%', 'Fe2O3_%', 'Cr_mgkg',
                                     'Ba_mgkg', 'Ni_mgkg', 'Cu_mgkg', 'Zn_mgkg', 'As_mgkg',
                                     'Se_mgkg', 'Mo_mgkg', 'Pb_mgkg', 'U_mgkg', 'Cd_mgkg',
                                     'Sn_mgkg', 'Sb_mgkg', 'Ce_mgkg']

def merge_dfs(input_dfs, northern_ireland_idx=None):
    """Merge the input dataframes, fixing the columns of the Northern Ireland dataframe.
    """
    if (northern_ireland_idx):
        fix_northern_ireland(input_dfs[northern_ireland_idx])
    return input_dfs[0].append(input_dfs[1:], ignore_index=True)

def run():
    """Main driver function.
    """
    if len(argv) < 4:
        raise TypeError('must pass output filepath, and at least two input filepaths')
    output_file = argv[1]
    input_files = argv[2:]

    input_dfs = []
    for input_file in input_files:
        input_dfs.append(pd.read_csv(input_file))

    merged_df = merge_dfs(input_dfs, northern_ireland_idx=0)

    merged_df.to_csv(output_file)

if __name__ == '__main__':

    run()
