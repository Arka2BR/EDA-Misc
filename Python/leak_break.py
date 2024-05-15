import os
from collections import OrderedDict
import pandas as pd

#Always Name your files "power_hvt"/"power_svt"/...


STOD 		= "/nfs/site/disks/w.aadhika1.673"
FILE_PATHS 	= ["/nfs/site/disks/w.aadhika1.673/idecode_baselines/maia_idecode_PDK005_160CH_0.49v_SUL_normSynth_m0zone_fix3_aadhika1_92/hvt_leakage.txt",
				"/nfs/site/disks/w.aadhika1.673/idecode_baselines/maia_idecode_PDK005_160CH_0.49v_SUL_normSynth_m0zone_fix3_aadhika1_92/svt_leakage.txt"] 

LIB_PTHS	= ["lib783_i0s_160h_50pp_bml_KLM/pdk050_r4v0p0_efv_context_simple/base_hvt/spice/lib783_ibs_160h_50pp_base_hvt.sp",
				"lib783_i0s_160h_50pp_bml_KLM/pdk050_r4v0p0_efv_context_simple/base_svt/spice/lib783_i0s_160h_50pp_base_svt.sp"]


def dir_gen(base, savefile):

	SAVEDIR_NAME= "Power_Reports"
	savedir		= os.path.join(base, SAVEDIR_NAME)
	save_path	= os.path.join(savedir, savefile)
	
	if not os.path.exists(savedir):
		os.mkdir(savedir)
		
	return save_path
	
def lkg_csv_gen(data, save_path, type=1):

	if type == 1:
		with open(save_path, 'w') as f:
			HEADER	= "Cell Name, Individual Leakage, Total Leakage, Instances\n"
			f.write(HEADER)
			for key, value in data.items():
				#print(item)
				f.write("{}, {}\n".format(key, value))
	elif type==2:
		data.to_csv(save_path, index = 'False')

	print("Successfully generated: {} !!!".format(save_path))

def z_csv_gen(data, save_path, type=1):

	if type==1:
		with open(save_path, 'w') as f:
				f.write("Cell Name, Z1/Z2/Z3 breakdown\n")
				for key, value in data.items():
					f.write("{}, {}\n".format(key, value))
	elif type==2:
		data.to_csv(save_path, index='False')	
	
	print("Successfully generated {} !!!".format(save_path))

def lib_z_breakdown(lib_path, cell_list, all_cells):
	with open(lib_path, 'r') as f:
		lib_data = f.readlines()
	
	Z_LIB		= {}
	VT_TYPE		= cell_list[0][-7]
	LIB_TYPE	= cell_list[0][1]
	
	for cell in all_cells:
		
		Z1, Z2, Z3 	= 0, 0, 0
		cell		= cell.format(LIB_TYPE, VT_TYPE)
		if cell in cell_list:
		
			#print(cell)
		
			START_FLAG 	= ".subckt {}".format(cell)
			END_FLAG  	= ".ends {}".format(cell)
			START_IDX	= [lib_data.index(line) for line in lib_data if line.startswith(START_FLAG)][0]
			END_IDX		= [lib_data.index(line) for line in lib_data if line.startswith(END_FLAG)][0]
			
			for line in lib_data[START_IDX+1 : END_IDX]:
				if not line.startswith("*"):
					line_lst 	= line.split()
					#print(line_lst)
					
					if len(line_lst[-4].split("=")[-1]) == 1:
					
						mono_Z	 	= int(line_lst[-4].split("=")[-1])
						mult		= int(line_lst[-2].split("=")[-1])
						finger		= int(line_lst[-1].split("=")[-1])
						if mono_Z == 1:
							Z1 += mult*finger
						elif mono_Z == 2:
							Z2 += mult*finger
						elif mono_Z == 3:
							Z3 += mult*finger
					
					
			Z_LIB[cell] = "{}/{}/{}".format(Z1, Z2, Z3) 

		else:
			Z_LIB[cell]	= "0/0/0"
			
		Z_LIB 		= OrderedDict(sorted(Z_LIB.items()))
		
	return Z_LIB
					
def leakage_breakdown(file):

	lkg_dict 		= {}
	cell_pwr_dict 	= {"Individual Lkg":0,
						"Total Lkg": 0,
						"Instances": 0
						}

	START_FLAG = "Clock Static Probability:  0.5000\n"
	END_FLAG   = "Power Distribution Summary"
	with open(file, 'r') as f:
		raw_data = f.readlines()
		
	START_INDEX = raw_data.index(START_FLAG) + 14
	END_INDEX 	= 0
	for line in raw_data:
		if END_FLAG in line:
			END_INDEX	= raw_data.index(line) - 5
	
	for i in range(START_INDEX, END_INDEX):
		len_flag = len(raw_data[i].split())
		
		cell_pwr_dict 	= {"Individual Lkg":0,
						"Total Lkg": 0,
						"Instances": 0
						}
		
		if len_flag > 1:
			line_lst 	= raw_data[i].split()
			lkg_pwr 	= float(line_lst[-4])
			cell_name	= line_lst[-1]
			
			if cell_name not in lkg_dict.keys():
				cell_pwr_dict["Individual Lkg"] 	= lkg_pwr
				cell_pwr_dict["Total Lkg"] 			= lkg_pwr
				cell_pwr_dict["Instances"]			= 1
				lkg_dict[cell_name]					= cell_pwr_dict
				
			else:
				lkg_dict[cell_name]["Total Lkg"] 	+= lkg_pwr
				lkg_dict[cell_name]["Instances"]	+= 1

	#print (lkg_dict)
	return lkg_dict	

def dataframe_gen(csv_paths):
	df_lst = []
	for path in csv_paths:
		df_temp = pd.DataFrame(pd.read_csv(path))
		if  (type(df_lst) == list and not df_lst) or  (type(df_lst) == pd.core.frame.DataFrame and df_lst.empty):
			df_lst = df_temp
		else:
			df_lst = pd.concat((df_lst, df_temp), axis=1)
	
	return df_lst
		
def col_dot_gen(data, col1, col2):
	tot_z1, tot_z2, tot_z3 			= [], [], []
	Cumul_Z1, Cumul_Z2, Cumul_Z3 	= 0, 0, 0
	for zb, inst in zip(data[col1][:-1], data[col2][:-1]):
		z_list 		= str(zb).strip().split("/")
		#print(z_list)
		if z_list != ['nan']:
			Total_Z1	= int(z_list[0])* inst
			Total_Z2	= int(z_list[1])* inst
			Total_Z3	= int(z_list[2])* inst
			
			Cumul_Z1	+= Total_Z1
			Cumul_Z2	+= Total_Z2
			Cumul_Z3	+= Total_Z3
		
		tot_z1.append(Total_Z1)
		tot_z2.append(Total_Z2)
		tot_z3.append(Total_Z3)
	tot_z1.append(Cumul_Z1)
	tot_z2.append(Cumul_Z2)
	tot_z3.append(Cumul_Z3)
	
	return tot_z1, tot_z2, tot_z3
	
def data_glue(data, index, cell_type):
	
	inner_keys 	= inner_keys = ["Individual Lkg", "Total Lkg", "Instances"]

	cell_data 	= ",".join([str(data[index][cell_type][x]) for x in inner_keys])
	cell_spec 	= "{},{}".format(cell_type, cell_data)
	
	return cell_spec

def lkg_preprocess(data, all_cells):
	outer_keys 		= [list(book.keys()) for book in data]
	
	SAVE_PTH_LST	= []	
	normalized_data	= []
	
	for i,datum in enumerate(data):
		total_power = 0
		total_inst  = 0
	
		VT_TYPE		= outer_keys[i][0][-7]
		LIB_TYPE	= outer_keys[i][0][1]
		print(LIB_TYPE)
		for cell in all_cells:
			cell = cell.format(LIB_TYPE, VT_TYPE)
			if cell not in outer_keys[i]:
				datum[cell] = "0, 0, 0"
			else:
				total_power += float(datum[cell]["Total Lkg"])
				total_inst  += int(datum[cell]["Instances"])
				datum[cell] = ",".join([str(datum[cell][x]) for x in datum[cell].keys()])
			
		datum 			= OrderedDict(sorted(datum.items()))
		
		datum["Total"] 	= ",{},{}".format(total_power, total_inst)
		normalized_data.append(datum)
		
		if VT_TYPE =='a': VT_NAME = 'ulvt'
		elif VT_TYPE =='b': VT_NAME = 'lvt'
		elif VT_TYPE =='c': VT_NAME = 'svt'
		elif VT_TYPE =='d': VT_NAME = 'hvt'
		
		
		save_path = dir_gen(STOD, "{}_{}_Lkg.csv".format(VT_NAME, i))
		SAVE_PTH_LST.append(save_path)
		
		lkg_csv_gen(datum, save_path)
		
	return SAVE_PTH_LST, normalized_data

def lkg_nexus(STOD):
	
	DATA 			= []
	SAVE_PTH_LST	= []
	cell_list		= []
	ALL_CELL 		= []
	df_lst			= []
	Z_LIB			= []
	IDENTIFIER		= []
	
	for i,item in enumerate(FILE_PATHS):
		
		IDENTIFIER.append(os.path.basename(item)[:-4])
	
		LKG_DATA 	= leakage_breakdown(item)
		cell_list.append(list(LKG_DATA.keys()))
		for item in cell_list[i]:
			FRONT_1		= item[0]
			FRONT_2		= item[2]
			MIDDLE		= item[3:-7]
			BACK		= item[-6:]
			#print(FRONT, MIDDLE, BACK)
			GEN_NAME	= f"""{FRONT_1}{{}}{FRONT_2}{MIDDLE}{{}}{BACK}"""
		
			if GEN_NAME not in ALL_CELL:
				ALL_CELL.append(GEN_NAME)
		
		ALL_CELL = sorted(ALL_CELL)
		#print(ALL_CELL)
		DATA.append(LKG_DATA)
		
	#Leakage Comparison CSV
	SAVE_PTH_LST, DATA 	= lkg_preprocess(DATA, ALL_CELL)
	LKG_FRAME			= dataframe_gen(SAVE_PTH_LST)
	LKG_SAVE_PATH 		= dir_gen(STOD, "Leakage_Comp.csv")
	lkg_csv_gen(LKG_FRAME, LKG_SAVE_PATH, 2)
	
	SAVE_PTH_LST = []
	for i, lib in enumerate(FILE_PATHS):
		IDENTIFIER = os.path.basename(lib)[:-4]
		if IDENTIFIER == 'power_hvt':
			Z_LIB.append(lib_z_breakdown(os.path.join(STOD, LIB_PTHS[i]), cell_list[i], ALL_CELL))	#TODO: Needs to be more robust
		elif IDENTIFIER == 'power_svt':
			Z_LIB.append(lib_z_breakdown(os.path.join(STOD, LIB_PTHS[i]), cell_list[i], ALL_CELL))
		elif IDENTIFIER == 'power_lvt':	
			Z_LIB.append(lib_z_breakdown(os.path.join(STOD, LIB_PTHS[2]), cell_list[i], ALL_CELL))
		elif IDENTIFIER == 'power_ulvt':
			Z_LIB.append(lib_z_breakdown(os.path.join(STOD, LIB_PTHS[3]), cell_list[i], ALL_CELL))
			
		SAVE_PATH	= dir_gen(STOD, "Cell_Z_Dist_{}_{}.csv".format(IDENTIFIER[i], i))	
		SAVE_PTH_LST.append(SAVE_PATH)
		# Create  Individual CSV
		z_csv_gen(Z_LIB[i], SAVE_PATH)
	
	
	# Z Comparison CSV
	Z_FRAME			= dataframe_gen(SAVE_PTH_LST)
	Z_SAVE_PATH		= dir_gen(STOD, "Cell_Z_Dist_Comp.csv")
	z_csv_gen(Z_FRAME, Z_SAVE_PATH, 2)
	
	#Combine Leakage and Z-distribution
	df_lst = []
	for path in [LKG_SAVE_PATH, Z_SAVE_PATH]:
		df_temp = pd.DataFrame(pd.read_csv(path))
		if  (type(df_lst) == list and not df_lst) or  (type(df_lst) == pd.core.frame.DataFrame and df_lst.empty):
			df_lst = df_temp
		else:
			#df_lst = pd.concat((df_lst, df_temp), axis=1)
			df_lst = df_lst.merge(df_temp,
                   on = "Cell Name", 
                   how = 'outer')
	
	Z_A	= col_dot_gen(df_lst, ' Z1/Z2/Z3 breakdown', ' Instances')
	df_lst['Total Z_1.A'],df_lst['Total Z_2.A'], df_lst['Total Z_3.A'] = Z_A
	Z_B = col_dot_gen(df_lst, ' Z1/Z2/Z3 breakdown.1', ' Instances.1')
	df_lst['Total Z_1.B'],df_lst['Total Z_2.B'], df_lst['Total Z_3.B'] = Z_B
	#print(df_lst)
		
	
	df_cols = ['Cell Name',
				' Individual Leakage',
				' Total Leakage',
				' Instances',
				' Z1/Z2/Z3 breakdown',
				'Total Z_1.A',
				'Total Z_2.A',
				'Total Z_3.A',
				'Cell Name.1_x',
				' Individual Leakage.1',
				' Total Leakage.1',
				' Instances.1',
				' Z1/Z2/Z3 breakdown.1',
				'Total Z_1.B',
				'Total Z_2.B',
				'Total Z_3.B'
				]
	df_append = df_lst[df_cols]
	FIN_SAVE_PATH	= dir_gen(STOD, "Cell_Z_Lkg_Comp.csv")
	z_csv_gen(df_append, FIN_SAVE_PATH, 2)
	
	
		

#########################################################################################################################

lkg_nexus(STOD)
#z_breakdown()