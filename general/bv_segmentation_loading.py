#this script is based on JK script to get a bloodvessel segmentation

def find_border_voxels_padded(data):
    # Pad the data with a border of 0s
    padded_data = np.pad(data, pad_width=1, mode='constant', constant_values=0)

    # Find the border voxels in the padded data
    padded_border_voxels = find_border_voxels(padded_data)

    # Remove the padding from the border voxels
    border_voxels = padded_border_voxels[1:-1, 1:-1, 1:-1]

    return border_voxels

import h5py
import numpy as np
from scipy import ndimage
from scipy.ndimage import zoom
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from numba import njit
import os as os
from syconn.handler.config import initialize_logging
#from mayavi import mlab
import open3d as o3d
import trimesh
from skimage import measure


f_name = 'cajal/scratch/users/arother/bio_analysis_results/general/230723_bv_seg_rendering'
log = initialize_logging('bv segmentation loading',
                             log_dir=f_name + '/logs/')
if not os.path.exists(f_name):
    os.mkdir(f_name)

hdf5_path = "/cajal/nvmescratch/projects/songbird/j0251/j0251_raw_near_iso_16x_ds_rfc_bloodvessel_seg.h5"
log.info(f'Step 1/5: Read data from hdf5 with path {hdf5_path}')
# Read the hdf5 file with a 3D matrix
with h5py.File( hdf5_path,"r") as f:
    data = f["dataset_1"][:]
data = zoom(data, (0.5,0.5,0.5), order=0)
mask = data == 2

dil_iterations = 2
log.info(f'Step 2/5: Perform closing operation with iterations = {dil_iterations}')
#make figure pre closing
plt.title('pre closing')
plt.imshow(mask[100,:,:])
plt.savefig(f'{f_name}/pre_closing.png')
plt.close()
mask = ndimage.binary_dilation(mask, iterations = dil_iterations)
mask = ndimage.binary_closing(mask)
plt.title('post closing')
plt.imshow(mask[100,:,:])
plt.savefig(f'{f_name}/post_closing.png')
plt.close()

log.info('Step 3/5: Get voxel number and boundary voxels from surface filtering')
labeled_mask, num_labels = ndimage.label(mask)
bv_seg = mask.astype(float)
log.info(f'num_labels: {num_labels}')
# Calculate the number of voxels in each connected component
component_voxel_counts = np.bincount(labeled_mask.ravel())

# Exclude the background (label 0) from the top connected components
component_voxel_counts[0] = 0

# Find the indices of the top 1000-largest connected components
top_indices100 = np.argsort(component_voxel_counts, )[-100:]
top_indices1000 = np.argsort(component_voxel_counts, )[-1000:]
# Create a mask for the top 1000-largest connected components
top_indices100 = np.isin(labeled_mask, top_indices100, invert=False)
top_indices1000 = np.isin(labeled_mask, top_indices1000, invert=False)
log.info(f'num bv voxels in top 100 components: {np.sum(top_indices100>0)}')
log.info(f'num background voxels top 100 components: {np.sum(top_indices100==0)}')
log.info(f'num bv voxels in top 1000 components: {np.sum(top_indices1000>0)}')
log.info(f'num background voxels top 1000 components: {np.sum(top_indices1000==0)}')

plt.title('pre surface filtering')
plt.imshow(top_indices100[100,:,:])
plt.savefig(f'{f_name}/pre_surface_filtering_top100.png')
plt.close()
plt.title('pre surface filtering')
plt.imshow(top_indices1000[100,:,:])
plt.savefig(f'{f_name}/pre_surface_filtering_top1000.png')
plt.close()
plt.title('pre surface filtering')
plt.imshow(bv_seg[100,:,:])
plt.savefig(f'{f_name}/pre_surface_filtering_alldata.png')
plt.close()

# only boundary voxels
@njit
def find_border_voxels(data):
    # Get the shape of the data
    z_len, y_len, x_len = data.shape

    # Initialize an empty array for border voxels
    border_voxels = np.zeros_like(data)

    # Iterate over the data
    for z in range(1, z_len - 1):
        for y in range(1, y_len - 1):
            for x in range(1, x_len - 1):
                # Check if the current voxel is a foreground voxel
                if data[z, y, x] == 1:
                    # Check the 26 neighboring voxels
                    for dz in range(-1, 2):
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                # Skip the current voxel
                                if dz == 0 and dy == 0 and dx == 0:
                                    continue
                                # If a neighboring voxel is a background voxel, mark the current voxel as a border voxel
                                if data[z + dz, y + dy, x + dx] == 0:
                                    border_voxels[z, y, x] = 1
                                    break
                            else:
                                continue
                            break
                        else:
                            continue
                        break

    return border_voxels

top_indices100_surface = find_border_voxels_padded(top_indices100)
top_indices1000_surface = find_border_voxels_padded(top_indices1000)
bv_seg_surface = find_border_voxels_padded(bv_seg)
log.info(f'num bv voxels surface only top 100: {np.sum(top_indices100_surface>0)}')
log.info(f'num bv voxels surface only top 1000: {np.sum(top_indices1000_surface>0)}')
log.info(f'num bv voxels surface only whole bv seg: {np.sum(bv_seg_surface>0)}')

plt.title('post surface filtering')
plt.imshow(top_indices100_surface[100,:,:])
plt.savefig(f'{f_name}/post_surface_filtering_top100.png')
plt.close()
plt.title('post surface filtering')
plt.imshow(top_indices1000_surface[100,:,:])
plt.savefig(f'{f_name}/post_surface_filtering_top1000.png')
plt.close()
plt.title('post surface filtering')
plt.imshow(bv_seg_surface[100,:,:])
plt.savefig(f'{f_name}/post_surface_filtering_bv_seg.png')
plt.close()

log.info('Step 4/5: create figure of results, also volume')

# Update the coordinates of the voxels with values above the threshold
#z, y, x = np.where(top_indices_surface)

# Create a histogram of the number of voxels in all the components
'''
plt.hist(component_voxel_counts, bins='auto')
plt.title("Histogram of voxel counts in connected components")
plt.xlabel("Number of voxels")
plt.ylabel("Frequency")
plt.savefig(f'{f_name}/hist_count_components.png')
plt.close()
'''

# Create a figure
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Get the coordinates of the voxels with values above the threshold
z, y, x = np.where(data == 2)

# Plot the voxels
ax.scatter(x[::10], y[::10], z[::10], c='b', marker='o', alpha=0.05, s=1)

# Set the axis labels
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')

# Show the plot
plt.savefig(f'{f_name}/bv_voxel_coords.png')
plt.close()
'''
# Create a figure
mlab.figure(bgcolor=(1, 1, 1))
# Prepare the volume data. Mayavi expects data in the form of a 3D array.
# Here we create a 3D array of zeros and set the voxels to 1.
vol_data = np.zeros((z.max()+1, y.max()+1, x.max()+1))
vol_data[z, y, x] = 1
# Perform volume rendering
mlab.pipeline.volume(mlab.pipeline.scalar_field(vol_data))
# Show the plot
plt.savefig(f'{f_name}/mlab_volume_scalar.png')
plt.close()
# Create a figure
mlab.figure(bgcolor=(1, 1, 1))
# Get the coordinates of the voxels with values above the threshold
# Plot the voxels
mlab.points3d(x[::5], y[::5], z[::5], mode='cube', color=(0, 0, 1), scale_factor=1)
# Set the axis labels
mlab.xlabel('X')
mlab.ylabel('Y')
mlab.zlabel('Z')
# Show the plot
plt.savefig(f'{f_name}/mlab_volume_3d.png')
plt.close()
# Run scipy label on the second largest ID to obtain connected components
# Get the indices of the 10 largest components
#ten_largest_indices = np.argsort(component_voxel_counts)[-10:]
# Print the number of voxels for the 10 largest components
#print("Number of voxels for the 10 largest components:")
#for idx in ten_largest_indices:
#    print(f"Component {idx}: {component_voxel_counts[idx]} voxels")
#for filtering
'''
log.info('Step 5/5: Create mesh from surfaces')
# Get the coordinates of the voxels with values above the threshold
z, y, x = np.where(top_indices100_surface)
# Combine the coordinates into a single array
points = np.column_stack((x, y, z))
#tranfer points to nm
points_nm = points * [320, 320, 400]
#tranfer to voxel data
points_vx = points_nm / [10, 10, 25]
#the following code on how to generate a mesh is not based on JK code but on a CHhatGPT suggestions from  AR
top_seg100 = top_indices100_surface.astype(float)
top_seg1000 = top_indices1000_surface.astype(float)
full_seg = bv_seg_surface.astype(float)
#from JH brain segmentation,
verts100, faces100, normals100, values100 = measure.marching_cubes(top_seg100, 0)
mesh100 = trimesh.Trimesh(verts100, faces100, validate=True)
output_file = f'{f_name}/bv_top100_surface_mesh.ply'
mesh100.export(output_file)
verts1000, faces1000, normals1000, values1000 = measure.marching_cubes(top_seg1000, 0)
mesh1000 = trimesh.Trimesh(verts1000, faces1000, validate=True)
output_file = f'{f_name}/bv_top1000_surface_mesh.ply'
mesh1000.export(output_file)
verts_bv, faces_bv, normals_bv, values_bv = measure.marching_cubes(full_seg, 0)
mesh_bv = trimesh.Trimesh(verts_bv, faces_bv, validate=True)
output_file = f'{f_name}/bv_full_seg_surface_mesh.ply'
mesh_bv.export(output_file)

log.info('Mesh of bloodvessels created and exported')

'''
#following code is again from JK and shows examples on how to use the coordinates for queries
from scipy.spatial import cKDTree


# Time the creation of the cKDTree
start = time.time()
tree = cKDTree(points)
end = time.time()
print(f'cKDTree creation took: {end - start} seconds')
# Run a few test queries
query_points = [(50, 50, 50), (100, 100, 100), (150, 150, 150)]
for query_point in query_points:
    start = time.time()
    dist, idx = tree.query(query_point)
    end = time.time()
    print(f'Query for point {query_point} took: {end - start} seconds')
    print(f'Nearest neighbor is at point {points[idx]} with distance {dist}')
'''