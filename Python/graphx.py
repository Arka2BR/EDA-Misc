import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib


#import multipolyfit as mpf

import os
import csv
import numpy as np
from scipy.interpolate import make_interp_spline


data_file 		= "/nfs/site/disks/w.aadhika1.894/fmax_Results/786_graphs/IFS_bsl5_WW26.7_BOOK.csv"
save_path_base 	= "/nfs/site/disks/w.aadhika1.894/fmax_Results/786_graphs/graphs"
csv_type 		= 1


def scatter_trend_gen(X, Y, color, savepath):


	X_val		= X[2:]
	Y_val 		= Y[2:]
	color_val	= color[2:]

	minima = min(color_val)
	maxima = max(color_val)
	
	norm 	= matplotlib.colors.Normalize(vmin=minima, vmax=maxima, clip=True)
	mapper 	= cm.ScalarMappable(norm=norm, cmap=cm.tab20)
	
	annote_set 	= list(set(color_val))
	usg_lst		= [0 for x in range(len(annote_set))]
	fig, ax = plt.subplots()
	
	for i in range(len(X_val)):
		
		x 			= X_val[i]
		y 			= Y_val[i]
		colour		= mapper.to_rgba(color_val[i])
		
		if usg_lst[annote_set.index(color_val[i])] == 0:
		
			ax.scatter(x,
			y,
			c=colour,
			cmap=cm.tab20,
			label= color_val[i])
			
			usg_lst[annote_set.index(color_val[i])] = 1
			
			#print(usg_lst)
			
		else:
			ax.scatter(x,
			y,
			color=colour,
			cmap=cm.tab20)
	
	
	plt.xlabel(X[0],
				fontweight ='bold', 
				size=12,
				color = "royalblue"
				)
				
	plt.ylabel(Y[0],
				fontweight ='bold',
				size=12,
				color = "royalblue"
				)	
				
	lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
	ax.grid(color = 'grey', linestyle = '--', linewidth = 0.5)
	
	#plt.show()
	
	plt.savefig(savepath, bbox_extra_artists=(lgd,), bbox_inches='tight')


def individual_trend_gen(X, Y, color, savepath_base):	

	X_val		= X[2:]
	Y_val 		= Y[2:]
	color_val	= color[2:]

	minima = min(color_val)
	maxima = max(color_val)
	
	norm 	= matplotlib.colors.Normalize(vmin=minima, vmax=maxima, clip=True)
	mapper 	= cm.ScalarMappable(norm=norm, cmap=cm.tab20)
	
	annote_set 	= list(set(color_val))
	usg_lst		= [0 for x in range(len(annote_set))]
	
	third_map   = {}
	
	#Assign keys
	for item in annote_set:
		third_map[item] = {}
	
	#Assign values
	for item in annote_set:
		third_map[item]['x'] = []
		third_map[item]['y'] = []
		for i in range(len(color_val)):
			if color_val[i] == item :
				third_map[item]['x'].append(X_val[i])
				third_map[item]['y'].append(Y_val[i])
				
	#Plot scatter charts based on items in annote_set
	
	for item in annote_set:
		savepath 	= os.path.join(save_path_base, f'{item}_{Y[0]}_trend.png')
		colour 		=  mapper.to_rgba(item)
		
		fig, ax 	= plt.subplots()
		
		x_t			= third_map[item]['x']
		y_t			= third_map[item]['y']
		
		x 			= np.array(x_t)
		y 			= np.array(y_t)
		
		
		#print(x_t, y_t)
		
		x_sort		= sorted(x_t)
		y_sort		= [j for i, j in sorted(zip(x_t, y_t))]
		
		print(x_sort, y_sort)
		
		X_Y_Spline 	= make_interp_spline(x_sort,y_sort)
		
		#print(X_Y_Spline)
		
		X_ 			= np.linspace(x.min(), x.max(), 500)
		Y_ 			= X_Y_Spline(X_)
		
		ax.scatter(x, y, color = colour, label = item)
		ax.plot(X_, Y_, color= colour)
		
		plt.xlabel(X[0], fontweight ='bold', size=12, color = "royalblue")
		plt.ylabel(Y[0], fontweight ='bold', size=12, color = "royalblue")
		lgd = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
		plt.grid(color = 'grey', linestyle = '--', linewidth = 0.5)
		

		

		#plt.show()
		
		plt.savefig(savepath, bbox_extra_artists=(lgd,), bbox_inches='tight')			
			

"""FMAX Plot generation"""

def fmax_plot_gen(datafile, savefilepath, csv_type):
	if csv_type == 1:
		Targ_FT_NAME	= "Target Frequency (GHz)"
		Ach_FT_NAME		= "Achieved Frequency (GHz)"
		UTIL_NAME		= "Post Route STD Cell Util"
		AREA_NAME		= "Floorplan Area"
	elif csv_type == 2:
		Targ_FT_NAME	= "clock freq (ghz)"
		Ach_FT_NAME		= "300th path"
		UTIL_NAME		= "utilization (%)"
		AREA_NAME		= "placeable area (sq. microns)"
	elif csv_type == 3:
		Targ_FT_NAME	= "Target Freq."
		Ach_FT_NAME		= "Achived Freq."
		UTIL_NAME		= "Utilization"
		AREA_NAME		= "Area"
		
	if not os.path.exists(savefilepath):
		os.mkdir(savefilepath)
	
	freq_trend		= os.path.join(savefilepath, 'Frequency_Trend.png')
	util_trend		= os.path.join(savefilepath, 'Utilization_Trend.png')
	area_trend		= os.path.join(savefilepath, 'Area_Trend.png')
	
	with open(datafile, 'r') as f:
		raw_data = f.readlines()
	
	for line in raw_data:
		line_lst = line[:-1].split(',')
		if line.startswith(Targ_FT_NAME):
			targ_freq = [float(line_lst[i]) if i > 0 else line_lst[i] for i in range(len(line_lst))]
		elif line.startswith(Ach_FT_NAME):
			ach_freq  = [float(line_lst[i]) if i > 0 else line_lst[i] for i in range(len(line_lst))]
		elif line.startswith(UTIL_NAME):
			util      = [float(line_lst[i]) if i > 0 else line_lst[i] for i in range(len(line_lst))]
		elif line.startswith(AREA_NAME):
			fp_area	  = [float(line_lst[i].strip()) if i > 0 else line_lst[i] for i in range(len(line_lst))]
	

	scatter_trend_gen(targ_freq, ach_freq, fp_area, freq_trend)		
	scatter_trend_gen(util, ach_freq, targ_freq, util_trend)
	scatter_trend_gen(fp_area, ach_freq, targ_freq, area_trend)	
	
	individual_trend_gen(targ_freq, ach_freq, fp_area, save_path_base)
	individual_trend_gen(util, ach_freq, targ_freq, util_trend)		


	
	
############################# EXECUTION #############################

		
fmax_plot_gen(data_file, save_path_base, csv_type = csv_type)
		
