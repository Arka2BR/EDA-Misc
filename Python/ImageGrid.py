'''Simple Image Grid Generator'''

# Name: Arkaprabho Adhikary
# Graduate Intern at TCDE,PPA Dept.

'''-------------------------------------------------------------------------------------------------------------------'''

import math
import os
import matplotlib.pyplot as plt

'''-------------------------------------------------------------------------------------------------------------------'''

# Configs:
images_dir = '/nfs/site/stod/stod3109/w.aadhika1.102/ImageGrid_temp'
result_grid_filename = '/nfs/site/stod/stod3109/w.aadhika1.102/ImageGrid_temp/UtilGrid.jpg'
result_figsize_resolution = 40 # 1 = 100px

'''-------------------------------------------------------------------------------------------------------------------'''

images_list = os.listdir(images_dir)
images_count = len(images_list)
print('Images: ', images_list)
print('Images count: ', images_count)

'''-------------------------------------------------------------------------------------------------------------------'''

# Calculate the grid size:
grid_size = math.ceil(math.sqrt(images_count))

'''-------------------------------------------------------------------------------------------------------------------'''

# Create plt plot:
fig, axes = plt.subplots(grid_size, grid_size, figsize=(result_figsize_resolution, result_figsize_resolution))

#Without the following code, axes will pop up in empty positions.
[axi.set_axis_off() for axi in axes.ravel()]

'''-------------------------------------------------------------------------------------------------------------------'''
# Place images in proper positions

current_file_number = 0
for image_filename in images_list:
    #Setup Coordinate System in Grid
    x_position = current_file_number // grid_size
    y_position = current_file_number % grid_size

    plt_image = plt.imread(images_dir + '/' + images_list[current_file_number])
    axes[x_position, y_position].imshow(plt_image)
    axes[x_position, y_position].set_title(f"Name: {image_filename}", y = 0.9, fontsize = 30, color = 'white', fontweight = 'bold')

    print((current_file_number + 1), '/', images_count, ': ', image_filename)
    current_file_number += 1

'''-------------------------------------------------------------------------------------------------------------------'''
# Adjust Subplots and Save output as an image

plt.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
plt.savefig(result_grid_filename)