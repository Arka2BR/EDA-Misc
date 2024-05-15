import os
from data_parser import data_parser, dict_warp_main, dict_warp_cell, main_csv_gen, cell_csv_gen
from collections import OrderedDict

#####################################################################
# IGNORE THESE BUT DONT COMMENT OUT 
#####################################################################

BLOCK 			= "deimos_vexecutive"

IDSID			= "aadhika1"

IDENTIFIER		= "test_run_160H"

TYPE 			= "isoperf"  #Can be either "isoperf" or "fmax"

NOW				= "WW04.1"

#####################################################################
#VARIABLES OF INTEREST
#####################################################################

STOD 			= "/nfs/site/disks/w.aadhika1.894"

RESULT_DIR		= os.path.join(STOD, f"SUH_PDK005_tool_exp")

REPORT			= "reports/postroute/qor.rpt"

PATH_LIST 		= [ "/nfs/site/disks/w.aadhika1.673/idecode_baselines/maia_idecode_PDK003_160CH_0.49v_SUL_normSynth_rebaseline_aadhika1_89/aadhika1_TBML_V2_hybrid_PDK003_160CH_0.49v_SUL_normSynth_rebaseline_89/{}".format(REPORT),
					"/nfs/site/disks/w.aadhika1.673/idecode_baselines/maia_idecode_PDK005_160CH_0.49v_SUL_normSynth_rebaseline_toolfix_aadhika1_91.5/aadhika1_TBML_V2_hybrid_PDK005_160CH_0.49v_SUL_normSynth_rebaseline_toolfix_91.5/{}".format(REPORT),
					"/nfs/site/disks/w.aadhika1.673/idecode_baselines/maia_idecode_PDK005_160CH_0.49v_SUL_normSynth_opt4b_toolfix_aadhika1_91.5/aadhika1_TBML_V2_hybrid_PDK005_160CH_0.49v_SUL_normSynth_opt4b_toolfix_91.5/{}".format(REPORT),
					"/nfs/site/disks/w.aadhika1.673/idecode_baselines/maia_idecode_PDK005_160CH_0.49v_SUL_normSynth_b1_bsline4_aadhika1_91.0/aadhika1_TBML_V2_hybrid_PDK005_160CH_0.49v_SUL_normSynth_b1_bsline4_91.0/{}".format(REPORT),
					"/nfs/site/disks/w.aadhika1.673/idecode_baselines/maia_idecode_PDK005_160CH_0.49v_SUL_normSynth_b2_bsline4_aadhika1_92.0/aadhika1_TBML_V2_hybrid_PDK005_160CH_0.49v_SUL_normSynth_b2_bsline4_92.0/{}".format(REPORT),
					"/nfs/site/disks/w.aadhika1.673/idecode_baselines/maia_idecode_PDK005_160CH_0.49v_SUL_normSynth_opt2p1_bsline_aadhika1_91.0/aadhika1_TBML_V2_hybrid_PDK005_160CH_0.49v_SUL_normSynth_opt2p1_bsline_91.0/{}".format(REPORT),
					"/nfs/site/disks/w.aadhika1.673/idecode_baselines/maia_idecode_PDK005_160CH_0.49v_SUL_normSynth_opt2p2_bsline_aadhika1_90.5/aadhika1_TBML_V2_hybrid_PDK005_160CH_0.49v_SUL_normSynth_opt2p2_bsline_90.5/{}".format(REPORT)
				]

CLASSIFIERS 	= [ "PDK003", "PDK005", "PDK005 opt4b", "PDK005 b1", "PDK005 b2", "PDK005 opt2p1", "PDK005 opt2p2"]

#####################################################################
#MAIN SCRIPT 
#####################################################################


main_csv_dict								= {}
cell_family_dict, cell_drive_dict	 		= {}, {}
cell_unit_dict								= {}
cell_main_dict								= {}
mod_main_dict								= {}
mod_cell_family_dict, mod_cell_drive_dict	= {}, {}
mod_cell_unit_area_dict						= {}


for path in PATH_LIST:

	"""Declare Paths"""
	
	RUN_PATH	= "/".join(path.split('/')[:-3])
	print(RUN_PATH)
	QOR_PATH 	= path
		
	dp = data_parser(RUN_PATH, TYPE, BLOCK, 1)
	#dp.global_parser()
	
	QOR = open(QOR_PATH, 'r')
	QOR_LINES = QOR.readlines()
	QOR.close()
	
	INDEX = PATH_LIST.index(path)
	
	#Cell distribution based on unit area of each distinct cell.
	cell_unit_dict[CLASSIFIERS[INDEX]] = dp.cell_parser(QOR_LINES, "UNIT_AREA")
	
	#Cell distribution based on logic families of each experiment. 
	cell_family_dict[CLASSIFIERS[INDEX]] = dp.cell_parser(QOR_LINES, "FAMILY")
	
	#Cell distribution based on drive strength of each experiment.
	cell_drive_dict[CLASSIFIERS[INDEX]] = dp.cell_parser(QOR_LINES, "DRIVE")
	
	#Cell Main
	cell_main_dict[CLASSIFIERS[INDEX]] = dp.cell_parser(QOR_LINES, "MAIN")
	
	
print("All run data has been successfully collected.")
print("Converting to CSV...")	
	
""" Modify the dicts for proper formatting"""

#Cell distribution based on logic families of all experiments. 
mod_cell_family_dict  	= dict_warp_cell(cell_family_dict, 2)

#Cell distribution based on drive strength of all experiments. 
mod_cell_drive_dict  	= dict_warp_cell(cell_drive_dict, 2)

#Cell distribution based on unit area of all experiments. 
mod_cell_unit_area_dict = dict_warp_cell(cell_unit_dict, 2)

#Cell distribution based on unit area of all experiments. 
mod_cell_main_dict 		= dict_warp_cell(cell_main_dict, 3)

#This dictionary has to be odered based on the keys
mod_cell_family_dict  	= OrderedDict(sorted(mod_cell_family_dict.items()))
mod_cell_drive_dict		= OrderedDict(sorted(mod_cell_drive_dict.items()))
mod_cell_unit_area_dict	= OrderedDict(sorted(mod_cell_unit_area_dict.items()))

#print(mod_cell_drive_dict)
	
"""Make the result directory"""

if os.path.basename(RESULT_DIR) not in os.listdir(STOD):
	os.mkdir(RESULT_DIR)


""" Genereate the Cell csv file"""

#Declare file paths.	
cell_family_file 	= 	os.path.join(RESULT_DIR, f"Cell_Family_Dist.csv")
cell_drive_file 	= 	os.path.join(RESULT_DIR, f"Cell_Drive_Dist.csv")
cell_unit_area_file = 	os.path.join(RESULT_DIR, f"Cell_Unit_Area.csv")
cell_main_file		=   os.path.join(RESULT_DIR, f"Cell_Main.xlsx")

#Generate CSVs

cell_csv_gen(cell_main_file, mod_cell_main_dict, ['Cell ID', 'Drive'], 'Family vs. Drive', 2)

print(cell_main_file)