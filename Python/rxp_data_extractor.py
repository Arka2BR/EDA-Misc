#################################################################### 
# Created by	: aadhika1 @ PPAC TCDE
# Date			: 12/26/2022
# Intended Tool	: CDNS Innovus
# Functionality	: Sweep Data Extraction 
# 
####################################################################

import os
import re
from collections import OrderedDict
from bs4 import BeautifulSoup
import requests
import tarfile
import gzip
from data_parser import data_parser, dict_warp_main, dict_warp_cell, isoperf_main_csv_gen, cell_csv_gen
import flow_template as ft
import user_template as ut



class rxp_data_gen():
	def __init__(self):
	
		###########################################################################################################################
		# USER VARS
		###########################################################################################################################
				
		self.BLOCK					= "enyo_issue"
					
		self.STOD					= "/nfs/site/disks/w.hegdesan.190"
					
		self.EXP_TYPE 				= "fmax"
					
		self.NOW					= "WW04.4"
					
		self.RESULT_DIR				= "Enyo_ID_TS_FMAX_data"
				
		self.RXP_BASE 				= "exps/a76_decode/New_customer/"
		#self.RXP_BASE				= "/nfs/site/stod/stod3109/w.guptasur.107/experiments" #General
				
		FILETAG						= "enyo_issue_78.3i0s_0.5beta_swp_"
		
		self.STD_CELL_BASE			= "/nfs/site/disks/w.hegdesan.190/exps/a76_decode/New_customer/inputs/collaterals/STDCELL_LIB"
		
		self.MAIN_CSV_NAME			= "ID_TS_160CH_PDK005.csv"
				
		self.IP_TYPE				= "Internal" #Specify what type of IP (Internal/External)
		
		self.STAGE					= "postroute"
		
		self.SUBSTAGE				= ""
		
		self.PARAMETERS				= 3 #How many parameters you swept for
		
		###########################################################################################################################
		# DERIVED VARS (Dont Touch if you don't know what you're doing...)
		###########################################################################################################################
		
		self.work_dir				= os.getcwd()
				
		self.BASE					= os.path.join(self.STOD, self.RXP_BASE)
		
		BASE_FILES					= os.listdir(self.BASE)
		
		#self.EXP_NAMES				= os.listdir(self.RXP_BASE) #General
		self.EXP_NAMES				= [os.path.join(self.BASE, x) for x in BASE_FILES if FILETAG in x ] #Custom
			
		#self.NAMES					= ["_".join(x.split("_")[-2:]) for x in self.EXP_NAMES] #General
		self.NAMES					= ["_".join(x.split("_")[-self.PARAMETERS:]) for x in self.EXP_NAMES] #Custom
		self.NAMES					= sorted(self.NAMES)	
				
		self.EXP_PATHS				= [os.path.join(self.RXP_BASE, pth) for pth in self.EXP_NAMES]
		self.EXP_PATHS				= sorted(self.EXP_PATHS)
		
		###########################################################################################################################
		# CONTAINERS
		###########################################################################################################################
		
		self.main_csv_dict			= {}
		self.mod_cell_family_dict	= {}
		self.mod_cell_drive_dict	= {}
		
		###########################################################################################################################
		# DEBUG
		###########################################################################################################################
		#print(self.EXP_NAMES)
		#print(self.NAMES)
		#print(self.EXP_PATHS)

	#################################################################### 
	# FILE FUNCS 
	####################################################################

	def file_data_retriever(self, path):
		if not path.endswith('.gz') :
			use_file 		= open(path, 'r')
			use_lines		= use_file.readlines()
			use_file.close() 
		else:
			use_file 		= gzip.open(path, 'rt')
			use_lines		= use_file.readlines()
			use_file.close()
		
		return use_lines
		
	def lib_preprocess(self):
		self.hvt_lib 	= os.path.join(self.libset, 'hvt/spice/lib783_ibs_160h_50pp_hvt.sp')
		self.hvt_data	= self.file_data_retriever(self.hvt_lib)
		self.svt_lib = os.path.join(self.libset, 'svt/spice/lib783_ibs_160h_50pp_svt.sp')
		self.svt_data	= self.file_data_retriever(self.svt_lib)
		self.lvt_lib = os.path.join(self.libset, 'lvt/spice/lib783_ibs_160h_50pp_lvt.sp')
		self.lvt_data	= self.file_data_retriever(self.lvt_lib)
		self.ulvt_lib = os.path.join(self.libset, 'ulvt/spice/lib783_ibs_160h_50pp_ulvt.sp')
		self.ulvt_data	= self.file_data_retriever(self.ulvt_lib)

	#################################################################### 
	# CALCULATION FUNCS 
	####################################################################
	
	"""Generates cell-wise Z dist. data"""
	
	def lib_z_breakdown(self, cell_list):

		for cell in cell_list:
			
			Z1, Z2, Z3 	= 0, 0, 0
			
			
			if cell not in ["g70shipidvm50digmifd01cdcdm4", "odi05top", "ip76d22wp0vrflp2r1w160x512be8"]:
				#print(cell)
				fullcell	= self.cell_type + cell
				#print(fullcell)
				cell_vt		= self.cell_dict[cell]["vt"]
				
				if cell_vt == 'a': lib_data = self.ulvt_data
				elif cell_vt == 'b': lib_data = self.lvt_data
				elif cell_vt == 'c': lib_data = self.svt_data
				elif cell_vt == 'd': lib_data = self.hvt_data
			
				START_FLAG 	= ".subckt {}".format(fullcell)
				END_FLAG  	= ".ends {}".format(fullcell)
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
						
						
				self.cell_dict[cell]["u_Z1"] = Z1 
				self.cell_dict[cell]["u_Z2"] = Z2 
				self.cell_dict[cell]["u_Z3"] = Z3 
				
				self.cell_dict[cell]["t_Z1"] = int(Z1) * int(self.cell_dict[cell]["count"])
				self.cell_dict[cell]["t_Z2"] = int(Z2) * int(self.cell_dict[cell]["count"])
				self.cell_dict[cell]["t_Z3"] = int(Z3) * int(self.cell_dict[cell]["count"])
	
			else:
				self.cell_dict[cell]["u_Z1"]	= 0
				self.cell_dict[cell]["u_Z2"]	= 0
				self.cell_dict[cell]["u_Z3"]	= 0
				
				self.cell_dict[cell]["t_Z1"]	= 0
				self.cell_dict[cell]["t_Z2"]	= 0
				self.cell_dict[cell]["t_Z3"]	= 0

	"""Generates Cell Family, Drive & Area Info"""
	
	def cell_parser(self, data, type):
	
	
		
		filename 		= os.path.join(self.work_dir, "cell_list.csv")
		
		
		STDCELL_BEGIN 	= "    Standard Cells in Netlist\n"
		STDCELL_END		= "# Pads:"
		START_INDEX 	= data.index(STDCELL_BEGIN)+ 3
		
		csv_list 		= []
		cell_dict		= {}
		
		self.BUFFER		= 0
		self.INVERTER	= 0
		
		
		
		for line in data[START_INDEX:]:
			if line.startswith(STDCELL_END):
				END_INDEX = data.index(line)
		
		for i in range(START_INDEX, END_INDEX):
			lst 		= data[i].split()
			
			cfn 		= lst[0] #Cell Full name
			if cfn.startswith('i0m') or cfn.startswith('i0s') or cfn.startswith('ibm') or cfn.startswith('ibs') :
				FAMILY		= cfn[3:-8]
				if any(x in cfn for x in ["bfn", "bfm", "bff",  "cbf"]):
					self.BUFFER += int(lst[1])
				elif any(x in cfn for x in ["inv"]):
					self.INVERTER += int(lst[1])
				
					
			else:
				FAMILY		= cfn[:-4]
				
			DRIVE		= cfn[-4:]
			
			inst		= int(lst[1])
			area		= float(lst[2])
			
			form       	= re.compile(r'^\d+x\d+')
			
			#Change the key to switch between driven strength and cell family
			if type == "DRIVE":
				key 		= DRIVE  

				if key not in cell_dict.keys() and (form.match(key) is not None):
					cell_dict[key] = [inst, area]
				elif (form.match(key) is not None):
					
					cell_dict[key][0] += inst
					cell_dict[key][1] += area
				
			elif type == "FAMILY":
				key			= FAMILY
				
				if key not in cell_dict.keys():
					cell_dict[key] = [inst, area]
				else:
					
					cell_dict[key][0] += inst
					cell_dict[key][1] += area
			else: 
				print("No such cell distribution type exists. CSV not generated!")
				
			
		return cell_dict
	
	"""Corner Achieved Freq. value based on corner & stage"""
	
	def fmax_gen(self, type): # Function used to calculate Internal Fmax
	
		path_group_flat = 'all'
	
		if type == "HOLD":
			input_file_ip = self.THOLD_LATE_PATH
		elif type== "SETUP":
			input_file_ip = self.TSETUP_LATE_PATH
			
		if not input_file_ip.endswith('.gz'):
			with open(input_file_ip) as f:
				content = f.readlines()
		else:
			with gzip.open(input_file_ip, 'rt') as f:
				content = f.readlines()


		hist_setup_all = {}
		actual_view = ""
		actual_group = ""
		actual_edge = 0
		actual_endpoint = ""
		actual_pba_slack = ""
		actual_endpoint_clock = ""
		min_period = 999999.0
		freq_list = []
		
		
		for x in content:
			if 'View:' in x:
				actual_view = str(x.split()[1]).rstrip()
			if 'Group:' in x:
				actual_group = str(x.split()[1]).rstrip()
			if 'Clock Edge:' in x:
				actual_edge = str(x.split()[2]).rstrip()
				freq_list.append(float(actual_edge))
			if 'Endpoint:' in x:
				actual_endpoint = str(x.split()[2]).rstrip()
			if 'Clock: (R)' in x:
				actual_endpoint_clock = str(x.split()[2]).rstrip()
			if 'Path ' in x and not 'Path Delay' in x:
				actual_pba_slack = str(x.split()[3].split('(')[1]).rstrip()
			if 'Slack:' in x:
				if 'all' in path_group_flat:
					hist_setup_all[actual_endpoint] = actual_pba_slack
				if 'reg2reg' in path_group_flat and not 'in2reg' in actual_group and not 'in2out' in actual_group and not 'reg2out' in actual_group:
					hist_setup_all[actual_endpoint] = actual_pba_slack
		
		min_period= max(freq_list,key=freq_list.count)
		
		if hist_setup_all:
			sorted_d =sorted(hist_setup_all.items(),key=lambda item: float(item[1]), reverse=False)
		
			#print(sorted_d[49])
			if self.STAGE == "postroute":
				slack_sum 	= sum(float(x[1]) for x in sorted_d) / 50         #Custom
				freq_50  = 10**3/float(float(min_period)+-1*float(slack_sum)) #Custom
				return freq_50
				
			elif self.STAGE == "opt_signoff":
				freq_100 = 10**3/float(float(min_period)+-1*float(sorted_d[100][1]))
				freq_500 = 10**3/float(float(min_period)+-1*float(sorted_d[500][1]))
				return freq_100 #Change depending on stage
	
	"""Calculates Depth based on corner & stage"""

	def gate_depth_gen(self, timing_file, N):
	
		self.GATE_CRIT_COUNT = 0
	
		if not timing_file.endswith('.gz'):
			with open(timing_file) as f:
				content = f.readlines()
		else:
			with gzip.open(timing_file, 'rt') as f:
				content = f.readlines()
		
		head_lst	= []
		
		for i, line in enumerate(content):
			line_lst = line.strip().split()
			#print()
			if line.strip().startswith("Group") and line_lst[1] == "reg2reg" :
				HEAD_INDEX = i + 27
				head_lst.append(HEAD_INDEX)
		
		for head in head_lst[:N - 1]:
			for i, line in enumerate(content[head:]):
				line_lst = line.strip().split()
				#print(len(line_lst) > 1)
				if len(line_lst) > 1 :
					
					if line_lst[3] == "clk->o":
						START_INDEX = i
				else:
					END_INDEX	= i
					break
			
			self.GATE_CRIT_COUNT += (END_INDEX - START_INDEX - 1)
			
		GATE_DEPTH = self.GATE_CRIT_COUNT / N
		return GATE_DEPTH
	
	
	
	def leg_counter(self, timing_file, N):
	
		leg_dict = {}
	
		if not timing_file.endswith('.gz'):
			with open(timing_file) as f:
				content = f.readlines()
		else:
			with gzip.open(timing_file, 'rt') as f:
				content = f.readlines()
		
		head_lst	= []
		
		for i, line in enumerate(content):
			line_lst = line.strip().split()
			#print()
			if line.strip().startswith("Group") and line_lst[1] == "reg2reg" :
				HEAD_INDEX = i + 27
				head_lst.append(HEAD_INDEX)
				
		for head in head_lst[:N - 1]:
			for i, line in enumerate(content[head + 1:]):
				line_lst = line.strip().split()
				if len(line_lst) > 1 :
					if "(net)" not in line_lst:
						cell_name = line_lst[5]
						cell_leg  = cell_name[-4:]
						if cell_leg not in leg_dict.keys():
							leg_dict[cell_leg] = 1
						else:
							leg_dict[cell_leg] += 1
						
				else:
					break
					
		#print(leg_dict)
		
		leg_dict = OrderedDict(sorted(leg_dict.items()))
		
		
		
		return leg_dict
	
	#################################################################### 
	# UTIL FUNCS 
	####################################################################
		
	def VT_rounder(self, vt):
		return round(float(vt/max(1,self.Total_VT) * 100), 2)
			
	#################################################################### 
	# EXTRACTION FUNCS 
	####################################################################
		
	def qor_extractor(self):

		PLACEMENT_INFO_START 		= "Floorplan/Placement Information\n"
		PLACE_INFO_START_INDEX		= self.qor_lines.index(PLACEMENT_INFO_START)
		WIRELENGTH_INFO_START		= "Wire Length Distribution\n"
		WIRELENGTH_INFO_END			= "Area of Power Net Distribution: \n"
		WIRELENGTH_INFO_START_INDEX = self.qor_lines.index(WIRELENGTH_INFO_START) + 2
		WIRELENGTH_INFO_END_INDEX   = self.qor_lines.index(WIRELENGTH_INFO_END) - 1
		
		'''Placement Data'''
		self.STD_CELL_AREA			= float(self.qor_lines[PLACE_INFO_START_INDEX + 3].split()[-2])
		self.STD_CELL_NOPHY_AREA	= float(self.qor_lines[PLACE_INFO_START_INDEX + 4].split()[-2])
		self.MACRO_AREA				= float(self.qor_lines[PLACE_INFO_START_INDEX + 5].split()[-2])
		self.BLOCKAGE_AREA			= float(self.qor_lines[PLACE_INFO_START_INDEX + 6].split()[-2])
		self.FP_AREA				= float(self.qor_lines[PLACE_INFO_START_INDEX + 8].split()[-2])
		self.PLACE_AREA				= self.FP_AREA - self.STD_CELL_NOPHY_AREA - self.MACRO_AREA - self.BLOCKAGE_AREA
		
		'''Wirelength Data'''
		self.WIRELENGTH_RAW_DATA	= self.qor_lines[WIRELENGTH_INFO_START_INDEX: WIRELENGTH_INFO_END_INDEX]
		
	def gate_depth_extractor(self):
	
		if self.STAGE == "postroute": self.CRIT_PATHS = 50
		elif self.STAGE == "opt_signoff": self.CRIT_PATHS = 100
	
		print("Calculating 1.1v corner Gate Depth...")
		self. GATE_HOLD_DEPTH = self.gate_depth_gen(self.THOLD_LATE_PATH, self.CRIT_PATHS)
		print("Calculating 0.65v corner Gate Depth...")
		self. GATE_SUT_DEPTH = self.gate_depth_gen(self.TSETUP_LATE_PATH, self.CRIT_PATHS)
		
		

	def leg_gen(self):
		if self.STAGE == "postroute": self.CRIT_PATHS = 50
		elif self.STAGE == "opt_signoff": self.CRIT_PATHS = 100
	
		print("Calculating 1.1v corner Legs...")
		self.LEG_HOLD_DICT = self.leg_counter(self.THOLD_LATE_PATH, self.CRIT_PATHS)
		HOLD_CSV_LEG	= os.path.join(self.FULL_RESULT_DIR, "Legs@1.1V.csv")
		self.leg_csv_gen(HOLD_CSV_LEG, self.LEG_HOLD_DICT)
		
		
		print("Calculating 0.65v corner Legs...")
		self.LEG_SUT_DICT = self.leg_counter(self.TSETUP_LATE_PATH, self.CRIT_PATHS)
		SETUP_CSV_LEG	= os.path.join(self.FULL_RESULT_DIR, "Legs@0.65V.csv")
		self.leg_csv_gen(SETUP_CSV_LEG, self.LEG_SUT_DICT)
		
	
	def drc_extraction(self):
		self.DRC 	= 0
		self.SHORTS = 0
		
		DRC_TYPES 	= [" EndOfLine Spacing",
		"EndOfLine Keepout",
		"Different Layer Cut Spacing",
		"Cut Forbidden Spacing",
		"Same Layer Cut Spacing",
		"ParallelRunLength Spacing",
		"Metal Short",
		"Metal Corner Spacing",
		"Metal EndofLine Spacing",
		"Cut Different Layer Spacing" ]
		
		if not "No DRC violations were found" in self.drc_lines:
			for line in self.drc_lines:
				if any(x in line for x in DRC_TYPES):
					self.DRC +=1
				if "Metal Short" in line:
					self.SHORTS +=1
				
		
	def flow_extractor(self):
	
		FT_INFO_START				= "Summary of flow:\n"
		
		
		if self.STAGE == "postroute":
			FT_INFO_START_INDEX			= self.flowtool_lines.index(FT_INFO_START) + 13
		elif self.STAGE == "opt_signoff":
			FT_INFO_START_INDEX			= self.flowtool_lines.index(FT_INFO_START) + 15
		FT_RAW_DATA					= self.flowtool_lines[FT_INFO_START_INDEX].replace(" ", "").split('|')
		
		
		self.STD_CELL_COUNT			= FT_RAW_DATA[-5]
		self.UTIL					= FT_RAW_DATA[-6]
		self.TNS					= FT_RAW_DATA[3]
		self.WNS					= FT_RAW_DATA[2]
		self.FEPS					= FT_RAW_DATA[4]
				
	
	def power_extractor(self, data):
	
	
		POWER_START 				= "Total Power \n"
		POWER_START_INDEX			= data.index(POWER_START)
		
		INTERNAL_POWER 				= data[POWER_START_INDEX + 2].split()[-2]
		SWITCHING_POWER				= data[POWER_START_INDEX + 3].split()[-2]
		LEAKAGE_POWER				= data[POWER_START_INDEX + 4].split()[-2]
		DYNAMIC_POWER				= str(float(INTERNAL_POWER) + float(SWITCHING_POWER))
		TOTAL_POWER					= data[POWER_START_INDEX + 5].split()[-1]
		
		SEQENTIAL_PWR				= float(data[POWER_START_INDEX + 12].split()[-2])
		COMBINATIONAL_PWR			= float(data[POWER_START_INDEX + 15].split()[-2])
		
	
		return INTERNAL_POWER, SWITCHING_POWER, LEAKAGE_POWER, DYNAMIC_POWER, TOTAL_POWER, SEQENTIAL_PWR, COMBINATIONAL_PWR

	def timing_extractor(self, corner):
		if corner == "SETUP":
			for line in self.setup_lines:
				#print("View : func_setup_test_corner" in line or "View : func_setup_low_corner" in line)
				if "View : func_setup_test_corner" in line or "View : func_setup_low_corner" in line:
					lst = line.split()
					#print(f"Line data: {lst}" )
					self.WNS_SUT 	= float(lst[-3])
					self.TNS_SUT 	= float(lst[-2])
					self.FEPS_SUT 	= int(lst[-1])
					break
		elif corner == "HOLD":
			for line in self.hold_lines:
				#print("View : func_hold_corner" in line or "View : func_setup_corner" in line)
				if "View : func_hold_corner" in line or "View : func_setup_corner" in line:
					lst = line.split()
					self.WNS_HOLD 	= float(lst[-3])
					self.TNS_HOLD 	= float(lst[-2])
					self.FEPS_HOLD 	= int(lst[-1])
					break
			
	def z_extractor(self):
		if self.z_dist_lines:
			Z_START						= "z1z2z3_type,ulvt,lvt,svt,hvt,Total_Xtor,Total_Xtor(%)\n"
			Z_START_INDEX				= self.z_dist_lines.index(Z_START)
			
			Z1_LINE						= self.z_dist_lines[Z_START_INDEX + 1].replace(" ", "").split(",")
			Z2_LINE						= self.z_dist_lines[Z_START_INDEX + 2].replace(" ", "").split(",")
			Z3_LINE						= self.z_dist_lines[Z_START_INDEX + 3].replace(" ", "").split(",")
			
			self.Z1_A					= int(Z1_LINE[1])
			self.Z1_B					= int(Z1_LINE[2])
			self.Z1_C					= int(Z1_LINE[3])
			self.Z1_D					= int(Z1_LINE[4])
			
			self.Z2_A					= int(Z2_LINE[1])
			self.Z2_B					= int(Z2_LINE[2])
			self.Z2_C					= int(Z2_LINE[3])
			self.Z2_D					= int(Z2_LINE[4])
			
			self.Z3_A					= int(Z3_LINE[1])
			self.Z3_B					= int(Z3_LINE[2])
			self.Z3_C					= int(Z3_LINE[3])
			self.Z3_D					= int(Z3_LINE[4])
			
			self.HVT 					= (self.Z1_D + self.Z2_D + self.Z3_D)
			self.SVT 					= (self.Z1_C + self.Z2_C + self.Z3_C)
			self.LVT 					= (self.Z1_B + self.Z2_B + self.Z3_B)
			self.ULVT 					= (self.Z1_A + self.Z2_A + self.Z3_A)
			
			self.Total_VT				= self.HVT + self.SVT + self.LVT + self.ULVT
			
			
		else:#Fail-safe for absence of Z report
			self.Z1_A					= 0
			self.Z1_B					= 0
			self.Z1_C					= 0
			self.Z1_D					= 0
										  
			self.Z2_A					= 0
			self.Z2_B					= 0
			self.Z2_C					= 0
			self.Z2_D					= 0
										  
			self.Z3_A					= 0
			self.Z3_B					= 0
			self.Z3_C					= 0
			self.Z3_D					= 0	
			
	def freq_extractor(self):
		if self.IP_TYPE == "External" :
			
			AVG300						= "#@ Begin verbose flow_step implementation.postroute.report_avg_300\n"
			
			for line in self.postroute_lines:
				if line.startswith("AVG Slack for 300 Paths is:"):
					self.AVG_WNS 				= float(line.split(':')[1])
			
			self.ACHIEVED_FREQUENCY		= round(1 / ((1 / self.TARGET_FREQ) - (self.AVG_WNS * 0.001)), 2)
			
			#self.FMAX_HOLD = self.fmax_gen("HOLD") #Extra
			#self.FMAX_SUT  = self.fmax_gen("SETUP")#Extra
		elif self.IP_TYPE == "Internal" :
			self.FMAX_HOLD = self.fmax_gen("HOLD")
			self.FMAX_SUT  = self.fmax_gen("SETUP")

	def fmax_data_extractor(self):
	
		filename	= os.path.join(self.work_dir, f"{self.BLOCK}_fmax_comp.csv")
		
		"""Find Placement Info and Layer Wirelength info from Qor File"""
		self.qor_extractor()
		
		"""Extract Total DRC and Short data"""
		self.drc_extraction()

		"""Parse flowtool.log for Utilization, DRC and STD Cell Count"""	
		self.flow_extractor()

		"""Parse Z-Distribution"""
		self.z_extractor()
		
		"""Parse Frquency Data"""
		self.freq_extractor()
		
		"""Dictionary generator"""
		
		
		
		if self.IP_TYPE == "External":
		
			"""Parse power_postroute.rpt"""
			self.INTERNAL_POWER, self.SWITCHING_POWER, self.LEAKAGE_POWER, self.DYNAMIC_POWER, self.TOTAL_POWER = self.power_extractor(self.power_lines)
			
			
		
			fmax_dict = {'Floorplan Area': self.FP_AREA,
							'Post Route Standard Cell Area': self.STD_CELL_AREA,
							'Post Route Standard Cell Count': self.STD_CELL_COUNT,
							'Post Route Standard Cell Utilization': self.UTIL,
							'DRC' : self.DRC,
							'Target Frequency': self.TARGET_FREQ,
							'Achieved Frequency': self.ACHIEVED_FREQUENCY,
							'Avg300 WNS (ps)': self.AVG_WNS,
							'TNS' :self.TNS,
							'WNS' :round(float(self.WNS), 2),
							'FEPS':self.FEPS,
							'HVT' : self.VT_rounder(self.HVT),
							'd Z1(%)': self.VT_rounder(self.Z1_D),
							'd Z2(%)': self.VT_rounder(self.Z2_D),
							'd Z3(%)': self.VT_rounder(self.Z3_D),
							'SVT' :	self.VT_rounder(self.SVT),
							'c Z1(%)': self.VT_rounder(self.Z1_C),
							'c Z2(%)': self.VT_rounder(self.Z2_C),
							'c Z3(%)': self.VT_rounder(self.Z3_C),
							'LVT' : self.VT_rounder(self.LVT),
							'b Z1(%)': self.VT_rounder(self.Z1_B),
							'b Z2(%)': self.VT_rounder(self.Z2_B),
							'b Z3(%)': self.VT_rounder(self.Z3_B),
							'ULVT': self.VT_rounder(self.ULVT),
							'a Z1(%)': self.VT_rounder(self.Z1_A),
							'a Z2(%)': self.VT_rounder(self.Z2_A),
							'a Z3(%)': self.VT_rounder(self.Z3_A),
							'Total Power': round(float(self.TOTAL_POWER), 2),
							'Internal Power' : round(float(self.INTERNAL_POWER), 2),
							'Leakage Power' : round(float(self.LEAKAGE_POWER), 2),
							'Switching Power': round(float(self.SWITCHING_POWER), 2),
							'Dynamic Power': round(float(self.DYNAMIC_POWER), 2)
							}
				
			print(self.WIRELENGTH_RAW_DATA)
			for line in self.WIRELENGTH_RAW_DATA:
				if self.WIRELENGTH_RAW_DATA.index(line) == len(self.WIRELENGTH_RAW_DATA)-1 :
					
					wire = line.split(':')
					
					fmax_dict[wire[0]] = round(float(wire[1].split()[0]), 2)
				else:
					wire = line.split()
					print(wire)
					fmax_dict[wire[1]] = round(float(wire[-2]), 2)				

		elif self.IP_TYPE == "Internal":
			"""Parse Power Info"""
			self.INTERNAL_POWER_SUT, self.SWITCHING_POWER_SUT, self.LEAKAGE_POWER_SUT, self.DYNAMIC_POWER_SUT, self.TOTAL_POWER_SUT, self.SEQENTIAL_PWR_SUT, self.COMBINATIONAL_PWR_SUT			= self.power_extractor(self.power_suh_lines)
			self.INTERNAL_POWER_HOLD, self.SWITCHING_POWER_HOLD, self.LEAKAGE_POWER_HOLD, self.DYNAMIC_POWER_HOLD, self.TOTAL_POWER_HOLD, self.SEQENTIAL_PWR_HOLD, self.COMBINATIONAL_PWR_HOLD 	= self.power_extractor(self.power_hold_lines)
			
			"""Gate Depth Extraction"""
			self.gate_depth_extractor()

			"""Cdyn Calc."""
			
			self.CDYN	= round(float(self.DYNAMIC_POWER_SUT) / self.FMAX_SUT, 2)
				
			
			
			
			"""Parse Timing Info"""
			self.timing_extractor('SETUP')
			self.timing_extractor('HOLD')
		
			'''Storage'''
			fmax_dict = {'Floorplan Area'									: self.FP_AREA,
							'Placeable Area (sq. um)'						: round(self.PLACE_AREA, 2),
							'Standard Cell Area'							: self.STD_CELL_AREA,
							'Standard Cell Count'							: self.STD_CELL_COUNT,
							'Buffer/Inv Count'								: "{}/{}".format(self.BUFFER, self.INVERTER),
							'Standard Cell Utilization'						: self.UTIL,
							'Macro Area (sq. um)'							: self.MACRO_AREA,
							'DRC/SHORTS' 									: "{}/{}".format(self.DRC, self.SHORTS),
							'Clock Freq. (0.65/1.1V) (GHz)'					: "{}/{}".format(self.TFREQ_SUT, self.TFREQ_HOLD),
							'Fmax @ 1.1V (GHz)'								: round(self.FMAX_HOLD,2),
							'Fmax @ 0.65V (GHz)'							: round(self.FMAX_SUT,2),
							'Total Power @ 1.1V (mW)'						: round(float(self.TOTAL_POWER_HOLD), 2),
							'Switching Power @ 1.1V (mW)'					: round(float(self.SWITCHING_POWER_HOLD), 2),
							'Dynamic Power @ 1.1V (mW)'						: round(float(self.DYNAMIC_POWER_HOLD), 2),
							'Leakage Power @ 1.1V (mW)' 					: round(float(self.LEAKAGE_POWER_HOLD), 2),
							'Total Power @ 0.65V (mW)'						: round(float(self.TOTAL_POWER_SUT), 2),
							'Switching Power @ 0.65V (mW)'					: round(float(self.SWITCHING_POWER_SUT), 2),
							'Dynamic Power @ 0.65V (mW)'					: round(float(self.DYNAMIC_POWER_SUT), 2),
							'Leakage Power @ 0.65V (mW)'					: round(float(self.LEAKAGE_POWER_SUT), 2),
							'Sequential Power @ 0.65V'						: round(self.SEQENTIAL_PWR_SUT, 2),
							'Combinational Power @ 0.65V'					: round(self.COMBINATIONAL_PWR_SUT, 2),
							'Cdyn @0.65v (mW/GHz)'							: round(self.CDYN, 2),
							'Total Z'										: self.Total_VT,
							'Z HVT/SVT/LVT/ULVT' 							: "{}/{}/{}/{}".format(self.HVT, self.SVT, self.LVT, self.ULVT),
							'HVT' 											: round(self.HVT, 2),
							'd Z1(%)'										: self.VT_rounder(self.Z1_D),
							'd Z2(%)'										: self.VT_rounder(self.Z2_D),
							'd Z3(%)'										: self.VT_rounder(self.Z3_D),
							'SVT' 											: round(self.SVT, 2),
							'c Z1(%)'										: self.VT_rounder(self.Z1_C),
							'c Z2(%)'										: self.VT_rounder(self.Z2_C),
							'c Z3(%)'										: self.VT_rounder(self.Z3_C),
							'LVT' 											: round(self.LVT, 2),
							'b Z1(%)'										: self.VT_rounder(self.Z1_B),
							'b Z2(%)'										: self.VT_rounder(self.Z2_B),
							'b Z3(%)'										: self.VT_rounder(self.Z3_B),
							'ULVT'											: round(self.ULVT, 2),
							'a Z1(%)'										: self.VT_rounder(self.Z1_A),
							'a Z2(%)'										: self.VT_rounder(self.Z2_A),
							'a Z3(%)'										: self.VT_rounder(self.Z3_A),
							'WNS @ 1.1V (ps)'								: round(self.WNS_HOLD, 2),
							'TNS @ 1.1V (ps)'								: round(self.TNS_HOLD, 2),
							'FEPS @ 1.1V'									: round(self.FEPS_HOLD, 2),
							'WNS @ 0.65V (ps)'								: round(self.WNS_SUT, 2),
							'TNS @ 0.65V (ps)'								: round(self.TNS_SUT, 2),
							'FEPS @ 0.65V'									: round(self.FEPS_SUT, 2),
							f'{self.CRIT_PATHS} path Gate Depth @ 1.1V'		: self.GATE_HOLD_DEPTH,
							f'{self.CRIT_PATHS} path Gate Depth @ 0.65V'	: self.GATE_SUT_DEPTH
							}
							
			#print(self.WIRELENGTH_RAW_DATA)
			for line in self.WIRELENGTH_RAW_DATA:
				if self.WIRELENGTH_RAW_DATA.index(line) == len(self.WIRELENGTH_RAW_DATA)-1 :
					
					wire = line.split(':')
					
					fmax_dict[wire[0]] = round(float(wire[1].split()[0]), 2)
				else:
					wire = line.split()
					#print(wire)
					fmax_dict[wire[1]] = round(float(wire[-2]), 2)
		return fmax_dict

	#################################################################### 
	# PARSER/REPORT GENERATOR FUNCS 
	####################################################################

	def global_parser(self, path):
	
		"""##################################           DEFINE PATHS            ########################################"""
	
		FT 						= sorted([filename for filename in os.listdir(path) if filename.startswith("flowtool.log")], reverse=True)[0]
		print(FT)
			
		self.QOR_PATH			= os.path.join(path, "reports/{}/qor.rpt".format(self.STAGE)) 
		#self.QOR_HTML_PATH		= os.path.join(path, "reports/qor.html")
		
		self.FLOWTOOL_PATH		= os.path.join(path, FT)
		self.POWER_PATH			= os.path.join(path, "power_postroute.rpt")
		self.DRC_PATH			= os.path.join(path, 'reports/{}/route.drc.rpt'.format(self.STAGE))
		#self.POWER_SUT_PATH	= os.path.join(path, "power_0P65V.rpt") #General
		self.POWER_SUT_PATH		= os.path.join(path, "power_setup_low.rpt")# Custom
		#self.POWER_HOLD_PATH	= os.path.join(path, "power_1P1V.rpt") #General
		self.POWER_HOLD_PATH	= os.path.join(path, "power_setup.rpt") # Custom
		self.HOLD_LOG_PATH		= os.path.join(path, ft.HOLD_RPT.format(self.STAGE))
		self.SETUP_LOG_PATH		= os.path.join(path, ft.SETUP_RPT.format(self.STAGE))
		
		if self.STAGE == "postroute":
			self.THOLD_LATE_PATH	= os.path.join(path, ft.POSTROUTE_REG2REG.format('func_setup_corner'))
			self.TSETUP_LATE_PATH	= os.path.join(path, ft.POSTROUTE_REG2REG.format('func_setup_low_corner'))
		elif self.STAGE == "opt_signoff":
			self.THOLD_LATE_PATH	= os.path.join(path, ft.SIGNOFF_REG2REG.format(self.BLOCK, 'func_setup_corner'))
			self.TSETUP_LATE_PATH	= os.path.join(path, ft.SIGNOFF_REG2REG.format(self.BLOCK, 'func_setup_low_corner'))
		
		
		if self.STAGE == "postroute":
			self.Z_DIST_PATH		= os.path.join(path, "z_summary_postroute.csv") 
		elif self.STAGE == "opt_signoff":
			self.Z_DIST_PATH		= os.path.join(path, "z_summary_optsignoff.csv") #General
			#self.Z_DIST_PATH		= os.path.join(path, "z_summary_postroute.csv") #Custom
		
		# TODO: This need to be generalized
		PR 						= sorted([filename for filename in os.listdir(os.path.join(path, "logs")) if filename.startswith("postroute.log") and not filename.startswith("postroute.logv")], reverse=True)[0]
		print(PR)
		self.POSTROUTE_LOG_PATH = os.path.join(path, f"logs/{PR}")
	
		"""##################################           RETRIVE DATA            ########################################"""
		
		ope = os.path.exists
		
		if self.IP_TYPE == "External":
			self.qor_lines 			= self.file_data_retriever(self.QOR_PATH)
			self.flowtool_lines 	= self.file_data_retriever(self.FLOWTOOL_PATH)
			self.power_lines 		= self.file_data_retriever(self.POWER_PATH)
			if ope(self.Z_DIST_PATH):
				self.z_dist_lines 	= self.file_data_retriever(self.Z_DIST_PATH)
			else: self.z_dist_lines = ""
			self.postroute_lines	= self.file_data_retriever(self.POSTROUTE_LOG_PATH)
			
		elif self.IP_TYPE == "Internal":
			self.qor_lines 			= self.file_data_retriever(self.QOR_PATH)
			self.drc_lines			= self.file_data_retriever(self.DRC_PATH)
			self.flowtool_lines 	= self.file_data_retriever(self.FLOWTOOL_PATH)
			self.power_suh_lines 	= self.file_data_retriever(self.POWER_SUT_PATH)
			self.power_hold_lines 	= self.file_data_retriever(self.POWER_HOLD_PATH)
			if ope(self.Z_DIST_PATH):
				self.z_dist_lines 	= self.file_data_retriever(self.Z_DIST_PATH)
			else:
				self.z_dist_lines	= ""
			self.postroute_lines	= self.file_data_retriever(self.POSTROUTE_LOG_PATH)
			self.setup_lines		= self.file_data_retriever(self.SETUP_LOG_PATH)
			self.hold_lines			= self.file_data_retriever(self.HOLD_LOG_PATH)
		
			
	
		"""##################################            EXECUTE                ########################################"""		
		
		self.cell_list_family	= self.cell_parser(self.qor_lines, "FAMILY")
		self.cell_list_drive	= self.cell_parser(self.qor_lines, "DRIVE")
		
		
		
		self.main_dict          = self.fmax_data_extractor()	

	def dict_warp_main(self, main_csv_dict):
	
		""" Modify the main dict"""
		outer_keys_cell	= list(main_csv_dict.keys())
		mod_main_dict = {}
		outer_keys_main	= main_csv_dict.keys()
		print(outer_keys_main)
		keys_main 		= main_csv_dict[outer_keys_cell[0]].keys()
		
		
		for key in keys_main :
			val_list			= []
			for okey in outer_keys_main:
				val_list.append(main_csv_dict[okey][key])
				
			mod_main_dict[key] = val_list
			
		return mod_main_dict
	
	def report_gen(self, path):
		
			
			NAME 				= "_".join(os.path.basename(path).split("_")[-3:-1])
			
			DIR_PATH 			= path
			
			#RUN_DIR			= "RunSynAPR_new" #General
			#self.RUN_PATH 		= os.path.join(DIR_PATH, RUN_DIR) #General
			self.RUN_PATH 		= DIR_PATH #Custom
			
			QOR_PATH 			= os.path.join(self.RUN_PATH, ft.QOR_RPT.format(self.STAGE))
			
			print(ft.SETUP_RPT.format(self.STAGE), self.STAGE)
			
			HOLD_PATH			= os.path.join(self.RUN_PATH, ft.HOLD_RPT.format(self.STAGE))
			SETUP_PATH			= os.path.join(self.RUN_PATH, ft.SETUP_RPT.format(self.STAGE))
			
			FT 					= sorted([filename for filename in os.listdir(self.RUN_PATH) if filename.startswith("flowtool.log")], reverse=True)[0]
			
			FT_PATH				= os.path.join(self.RUN_PATH, FT)
			SUMMARY				= ft.SUMMARY
			
			if self.IP_TYPE == 'External': 
				self.TARGET_FREQ	= float(os.path.basename(path).split("_")[-1])
			elif self.IP_TYPE == "Internal":
				self.TARGET_FREQ	= float(os.path.basename(path).split("_")[-2])
				self.TFREQ_SUT 		= float(os.path.basename(path).split("_")[-2])
				self.TFREQ_HOLD		= float(os.path.basename(path).split("_")[-3])
			
			print(FT_PATH)
			
			"""Check if all the runs have finished"""
			
			print("Beginning flow completion wait...")
			gen_stat	= True
			while gen_stat:
				if os.path.exists(FT_PATH):
					
					FT_FILE     = open(FT_PATH, 'r')
					FT_LINES	= FT_FILE.readlines()
					FT_COND		= SUMMARY in FT_LINES
					FT_FILE.close()
					
					
					
					if os.path.exists(QOR_PATH) and FT_COND and os.path.getsize(QOR_PATH) > 0 :
					
						print(f"{NAME} run Successfully Completed!")
						print(ft.COLLECT_DATA)
					
						
						self.global_parser(self.RUN_PATH)
						
						print(f"Data collected for: {NAME}")
						
						self.main_csv_dict[NAME] = self.main_dict
						self.mod_cell_family_dict[NAME] = self.cell_list_family
						self.mod_cell_drive_dict[NAME] = self.cell_list_drive
						
						gen_stat = False
					else:
						gen_stat = True
	
	def main_csv_gen(self, filepath, data, NAMES, Z_TYPES, Z_VOLTAGES):
	
		with open(filepath, "w") as f:
			f.write(f"Parameter, {', '.join(map(str, NAMES))}\n")
			f.write("\n")
			for key in data.keys():
			
				if key.split()[-1] in Z_TYPES:
					if key.split()[0] in Z_VOLTAGES:
						f.write(f"{key}, {', '.join(map(str, data[key]))}\n")
				else:
					f.write(f"{key}, {', '.join(map(str, data[key]))}\n")
			
		print(f"{filepath} generated successfully.")
	
	def cell_csv_gen(self, filepath, data, NAMES, format=1):

		combo_names = NAMES
		
		
		with open(filepath, "w") as f:
			
			sub_heads = ['Instance', 'Area(um^2)']
			
			if format == 1:
				f.write(f"Cell Family,, {',,'.join(map(str, combo_names))}\n")
				f.write(f", { ','.join(sub_heads * len(combo_names))}\n" )
			elif format == 2:
				f.write(f"Cell Family, {','.join(map(str, combo_names * len(sub_heads)))}\n")
				head_frmt = [',' * (len(combo_names) -1) + sh for sh in sub_heads]
				f.write(f",{ ','.join(head_frmt)}\n" )
			elif format == 3:
				f.write(f"Drive Strength, {','.join(map(str, combo_names * len(sub_heads)))}\n")
				head_frmt = [',' * (len(combo_names) -1) + sh for sh in sub_heads]
				f.write(f",{ ','.join(head_frmt)}\n" )
			for key in data.keys():
				f.write(f"{key}, {', '.join(data[key])}\n")
		print(f"{filepath} generated successfully.")

	def leg_csv_gen(self, filepath, data):
		with open(filepath, 'w') as f:
			f.write("Leg Type, Instances\n")
			for key, values in data.items():
				f.write("{}, {}\n".format(key, values))
				
		print("Successfully generated {} !!!".format(filepath))
	
	#################################################################### 
	# CALL 
	####################################################################
	def __call__(self):
			
		BLACKLIST = []
		
		
		for path in self.EXP_PATHS:
			bn 		= os.path.basename(path)
			name	= "_".join(bn.split("_")[-2:])
			if name not in BLACKLIST:
				self.report_gen(path)
		
			
		""" Modify the dicts for proper formatting"""
			
		mod_main_dict  			= dict_warp_main(self.main_csv_dict)
		
		mod_cell_family_dict  	= dict_warp_cell(self.mod_cell_family_dict, 2) 
		mod_cell_drive_dict		= dict_warp_cell(self.mod_cell_drive_dict, 2)
		
		
		#These dictionaries have to be odered based on the keys
		mod_cell_family_dict  	= OrderedDict(sorted(mod_cell_family_dict.items()))
		mod_cell_drive_dict		= OrderedDict(sorted(mod_cell_drive_dict.items()))
			
		"""Make the result directory"""
		TSTOD = "/nfs/site/stod/stod3109/w.aadhika1.102" #Temporary directory path. Comment out when not testing
		#TSTOD = self.STOD #Use self.STOD in general
		if os.path.basename(self.RESULT_DIR) not in os.listdir(TSTOD):  
		
			
			os.mkdir(os.path.join(TSTOD, self.RESULT_DIR))
		
		"""Generate the Main csv file"""
			
		self.FULL_RESULT_DIR	= os.path.join(TSTOD, self.RESULT_DIR)	
		main_csv 				= os.path.join(self.FULL_RESULT_DIR, self.MAIN_CSV_NAME)
																			
		self.main_csv_gen(main_csv,
							mod_main_dict,
							self.NAMES,
							ut.Z_TYPES,
							ut.Z_VOLTAGES
							)
							
		""" Genereate the Cell csv file"""
			
		cell_family_csv_file 	= 	os.path.join(self.FULL_RESULT_DIR, ft.CELL_FAMILY_CSV.format(self.RESULT_DIR,
																					 self.EXP_TYPE,
																					 self.NOW
																					 )
																					 )
																					 
		cell_drive_csv_file 	= 	os.path.join(self.FULL_RESULT_DIR, ft.CELL_DRIVE_CSV.format(self.RESULT_DIR,
																					 self.EXP_TYPE,
																					 self.NOW
																					 )
																					 )
		
		self.cell_csv_gen(cell_family_csv_file, mod_cell_family_dict, self.NAMES, 2)
		self.cell_csv_gen(cell_drive_csv_file, mod_cell_drive_dict, self.NAMES, 3)
		
		"""Leg Count Generator"""	
		self.leg_gen()
						
'''Main'''						
if __name__ == "__main__":
	fl = rxp_data_gen()
	fl()
