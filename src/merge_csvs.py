#!/usr/bin/env python
"""Join stream sediment data from different Tellus surveys
into a single CSV file to ease later processing.
"""

import argparse
import pandas as pd

def merge_dfs(input_dfs, northern_ireland_idx=None):
    """Merge the input dataframes.
    """
    return input_dfs[0].append(input_dfs[1:], ignore_index=True)

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

def fix_northern_ireland(input_dfs, ni1idx, ni2idx, niauandpgeidx):
    """Modify Northern Ireland columns to match Republic ones.
    """

    if (ni1idx != None):
        if (0 <= ni1idx < len(input_dfs)):
            fix_northern_ireland_set1(input_dfs[ni1idx])
        else:
            raise ValueError('ni1idx should be between 0 and the number of input files')

    if (ni2idx != None):
        if 0 <= ni2idx < len(input_dfs):
            fix_northern_ireland_set2(input_dfs[ni2idx])
        else:
            raise ValueError('ni2idx should be between 0 and the number of input files')

    if (niauandpgeidx != None):
        if 0 <= niauandpgeidx < len(input_dfs):
            fix_northern_ireland_auandpge(input_dfs[niauandpgeidx])
        else:
            raise ValueError('niauandpgeidx should be between 0 and the number of input files')

    # Remove partial Northern Ireland dataframes from input_dfs list and join them.
    # This is done after the above steps as
    # popping from input_dfs changes the index position of dataframes 
    ni_list = []

    if (ni1idx != None):
            ni_list.append(ni1idx)
    if (ni2idx != None):
            ni_list.append(ni2idx)
    if (niauandpgeidx != None):
            ni_list.append(niauandpgeidx)

    if len(ni_list) > 1:
        for idx in ni_list:
            input_dfs[idx].set_index(['Sample_ID', 'Easting', 'Northing'], inplace=True)
        ni_df = input_dfs[ni_list[0]].join([input_dfs[i] for i in ni_list[1:]],how='outer')
        ni_df.reset_index(inplace=True)
        for index in sorted(ni_list, reverse=True):
            del input_dfs[index]
        input_dfs.append(ni_df)
    return input_dfs
    

def run(output_file, input_files, ni1idx, ni2idx, niauandpgeidx):
    """Main driver function.
    """
    input_dfs = []
    for input_file in input_files:
        input_dfs.append(pd.read_csv(input_file))

    input_dfs = fix_northern_ireland(input_dfs, ni1idx, ni2idx, niauandpgeidx)

    merged_df = merge_dfs(input_dfs)

    merged_df.to_csv(output_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=str, help="path to output merged file")
    parser.add_argument("inputs", type=str, help="paths to files to be merged", nargs='+')
    parser.add_argument("--ni1idx", type=int, help="index of Northern Ireland Set 1 in input list")
    parser.add_argument("--ni2idx", type=int, help="index of Northern Ireland Set 2 in input list")
    parser.add_argument("--niauandpgeidx", type=int, help="index of Northern Ireland Au and PGE in input list")
    args = parser.parse_args()
    run(args.output, args.inputs, args.ni1idx, args.ni2idx, args.niauandpgeidx)
