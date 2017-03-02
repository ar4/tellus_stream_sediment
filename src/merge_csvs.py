#!/usr/bin/env python
"""Join stream sediment data from different Tellus surveys
into a single CSV file to ease later processing.
"""

import argparse
import pandas as pd

def fix_northern_ireland_set1(northern_ireland_set1_data):
    """Modify Northern Ireland columns in 'set1' to match Republic ones.
    """
    northern_ireland_set1_data.drop(['YEAR', 'LABNO'], axis=1, inplace=True)
    northern_ireland_set1_data.columns = ['Sample_ID', 'Easting', 'Northing', 'MgO_%',
                                     'P2O5_%', 'K2O_%', 'CaO_%', 'MnO_%', 'Fe2O3_%', 'Cr_mgkg',
                                     'Ba_mgkg', 'Ni_mgkg', 'Cu_mgkg', 'Zn_mgkg', 'As_mgkg',
                                     'Se_mgkg', 'Mo_mgkg', 'Pb_mgkg', 'U_mgkg', 'Cd_mgkg',
                                     'Sn_mgkg', 'Sb_mgkg', 'Ce_mgkg']

def fix_northern_ireland_set2(northern_ireland_set2_data):
    """Modify Northern Ireland columns in 'set2' to match Republic ones.
    """
    northern_ireland_set2_data.drop(['YEAR', 'LABNO'], axis=1, inplace=True)
    northern_ireland_set2_data.columns = ['Sample_ID', 'Easting', 'Northing', 'TiO2_%',
                                          'V_mgkg', 'Co_mgkg', 'Ga_mgkg', 'Rb_mgkg', 'Sr_mgkg',
                                          'Y_mgkg', 'Zr_mgkg', 'Nb_mgkg', 'Bi_mgkg', 'Th_mgkg',
                                          'Ag_mgkg', 'Cs_mgkg', 'La_mgkg']

def fix_northern_ireland_auandpge(northern_ireland_auandpge_data):
    """Modify Northern Ireland columns in 'Au and PGE' to match Republic ones.
    """
    northern_ireland_auandpge_data.columns = ['Sample_ID', 'Easting', 'Northing', 'Au_ugkg',
                                              'Pt_ugkg', 'Pd_ugkg']

def fix_northern_ireland_boron(northern_ireland_boron_data):
    """Modify Northern Ireland columns in 'Boron' to match Republic ones.
    """
    northern_ireland_boron_data.columns = ['Sample_ID', 'Easting', 'Northing', 'B_mgkg']

def merge_dfs(input_dfs, northern_ireland_idx=None):
    """Merge the input dataframes, fixing the columns of the Northern Ireland dataframe.
    """
    if (northern_ireland_idx):
        fix_northern_ireland(input_dfs[northern_ireland_idx])
    return input_dfs[0].append(input_dfs[1:], ignore_index=True)

def fix_northern_ireland(input_dfs, ni1idx, ni2idx, niauandpgeidx, niboronidx):
    """Modify Northern Ireland columns to match Republic ones and merge.
    """
    if (ni1idx):
        if 1 <= ni1idx <= len(input_files):
            fix_northern_ireland_set1(input_dfs[ni1idx])
        else:
            raise ValueError('ni1idx should be between 1 and the number of input files')

    if (ni2idx):
        if 1 <= ni2idx <= len(input_files):
            fix_northern_ireland_set2(input_dfs[ni2idx])
        else:
            raise ValueError('ni2idx should be between 1 and the number of input files')

    if (niauandpgeidx):
        if 1 <= niauandpgeidx <= len(input_files):
            fix_northern_ireland_auandpge(input_dfs[niauandpgeidx])
        else:
            raise ValueError('niauandpgeidx should be between 1 and the number of input files')

    if (niboronidx):
        if 1 <= niboronidx <= len(input_files):
            fix_northern_ireland_boron(input_dfs[niboronidx])
        else:
            raise ValueError('niboronidx should be between 1 and the number of input files')

def run(output_file, input_files, ni1idx, ni2idx, niauandpgeidx, niboronidx):
    """Main driver function.
    """
    input_dfs = []
    for input_file in input_files:
        input_dfs.append(pd.read_csv(input_file))

    inputs_dfs = fix_northern_ireland(input_dfs, ni1idx, ni2idx, niauandpgeidx, niboronidx)

    merged_df = merge_dfs(input_dfs, ni1idx, ni2idx, niauandpgeidx, niboronidx)

    merged_df.to_csv(output_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=str, help="path to output merged file", required=True)
    parser.add_argument("inputs", type=str, help="paths to files to be merged", required=True)
    parser.add_argument("--ni1idx", type=int, help="index of Northern Ireland Set 1 in input list")
    parser.add_argument("--ni2idx", type=int, help="index of Northern Ireland Set 2 in input list")
    parser.add_argument("--niauandpgeidx", type=int, help="index of Northern Ireland Au and PGE in input list")
    parser.add_argument("--niboronidx", type=int, help="index of Northern Ireland Boron in input list")
    args = parser.parse_args()
    run(args.output, args.inputs, args.ni1idx, args.ni2idx, args.niauandpgeidx, args.niboronidx)
