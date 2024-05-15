#!/usr/bin/python3

#######################################################################
# Created by: aadhika1
# Last Update: 7/31/2023
# Description: Converts SNPS Don't Use List to CDNS consumable format.
######################################################################


import os
import argparse

def du_conv():
    # Parser Setup
    parser  = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--file", help="input file (should be dont_use.tcl for SNPS)")
    parser.add_argument("-lp", "--libprefix", help="Library Prefix to append to cell name")
    parser.add_argument("-od", "--outputdir", help="Specify base directory for output file to be stored in.")
    args    = parser.parse_args()

    config  = vars(args)

    if any(value == None for value in config.values()):
        print("\u001b[31;1mRequired arguments not supplied. Make use all 3 argument [-f], [-lp], [-od] are specified. Conversion can't proceed... \u001b[0m")
    else:
        # Arg Parse
        SRC_PTH     = config['file']
        LIB_PREFIX  = config['libprefix']
        OP_DIR      = config['outputdir']

        # Fixed file name for CDNS
        DU_OP_FILE  = "dont_use_cdns.list"
        OP_PTH      = os.path.realpath(os.path.join(OP_DIR, DU_OP_FILE))


        # Store all raw data here
        with open(SRC_PTH , 'r') as f:
            raw_data = f.readlines()

        #Filter the dont_use list and write into output file.
        with open(OP_PTH, 'w') as f:
            for i, line in enumerate(raw_data):

                if "${fdk_lib}" in line and "#" not in line:
                    cell_fam    = line.split()[0].strip('"').split('}')[-1]
                    cell_name   = "{}{}\n".format(LIB_PREFIX, cell_fam)
                    f.write(cell_name)
            print("\u001b[32;1mGenerated output: \u001b[35;1m {}\n \u001b[0m".format(OP_PTH))
           

if __name__ == "__main__":
    du_conv()
