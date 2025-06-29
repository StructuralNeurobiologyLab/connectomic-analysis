from syconn.reps.super_segmentation import SuperSegmentationObject
from syconn.proc.meshes import write_mesh2kzip, compartmentalize_mesh_fromskel, make_ply_string_wocolor
from analysis_params import Analysis_Params
import numpy as np


def whole_cellid2mesh(cell_input):
    '''
    exports cell as k-zip mesh file
    :param cell_input: cellid, foldername, version of working dir
    :return:
    '''

    cellid, f_name, version, with_skel, ply_only = cell_input
    bio_params = Analysis_Params(version=version)
    ct_dict = bio_params.ct_dict(with_glia=True)
    cell = SuperSegmentationObject(cellid)
    cell.load_attr_dict()
    ct_num = cell.attr_dict['celltype_pts_e3']
    celltype = ct_dict[ct_num]
    indices, vertices, normals = cell.mesh
    if ply_only:
        ply_name = f'{f_name}/{cellid}_{celltype}_mesh.ply'
        make_ply_string_wocolor(ply_name, indices.astype(np.float32), vertices.astype(np.float32))
    else:
        kzip_out = f'{f_name}/{cellid}_{celltype}_mesh'
        write_mesh2kzip(kzip_out, indices.astype(np.float32), vertices.astype(np.float32), normals, None,
                        f'{cellid}.ply')
    if with_skel:
        kzip_out_skel = f'{f_name}/{cellid}_skel'
        cell.save_skeleton_to_kzip(kzip_out_skel)

def comp2mesh(cell_input):
    '''
    Exports k.zip files of the meshes of desired cell compartments based on skeleton prediction
    :param cell_input: cellid, foldername, version, list of desired compartmens
    :return:
    '''
    cellid, f_name, version, compartments, ply_only = cell_input
    bio_params = Analysis_Params(version=version)
    ct_dict = bio_params.ct_dict(with_glia=True)
    cell = SuperSegmentationObject(cellid)
    cell.load_attr_dict()
    ct_num = cell.attr_dict['celltype_pts_e3']
    celltype = ct_dict[ct_num]
    cell.load_skeleton()
    compartment_mesh = compartmentalize_mesh_fromskel(cell)
    for comp in compartments:
        comp_inds, comp_verts, comp_norms = compartment_mesh[comp]
        if ply_only:
            ply_name = f'{f_name}/{cellid}_{celltype}_mesh.ply'
            make_ply_string_wocolor(ply_name, comp_inds.astype(np.float32), comp_verts.astype(np.float32))
        else:
            kzip_out = f'{f_name}/{cellid}_{celltype}_{comp}_mesh'
            write_mesh2kzip(kzip_out, comp_inds.astype(np.float32), comp_verts.astype(np.float32), comp_norms, None,
                            f'{cellid}.ply')