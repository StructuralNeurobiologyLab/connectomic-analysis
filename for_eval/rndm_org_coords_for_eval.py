#similar to select_random_vesicles_for_eval
#select random er coordinates for eval
#have to get from the meshes as only one rep_coord per cell mapped


if __name__ == '__main__':
    import time
    from syconn.handler.config import initialize_logging
    from syconn import global_params
    from syconn.reps.segmentation import SegmentationDataset
    from syconn.reps.super_segmentation import SuperSegmentationObject
    from cajal.nvmescratch.users.arother.bio_analysis.general.vesicle_helper import \
        get_vesicle_distance_information_per_cell
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_params import Analysis_Params
    import os as os
    import pandas as pd
    import numpy as np
    from tqdm import tqdm
    from syconn.mp.mp_utils import start_multiprocess_imap
    from sklearn.utils import shuffle

    version = 'v6'
    bio_params = Analysis_Params(version=version)
    global_params.wd = bio_params.working_dir()
    organelle = 'golgi'
    if organelle != 'single vesicle':
        sd_org = SegmentationDataset(organelle, working_dir=global_params.config.working_dir)
    ct_dict = bio_params.ct_dict(with_glia = True)
    n_samples = 15
    gt_version = 'v7'
    color_key = 'TePkBr'
    f_name = f"cajal/scratch/users/arother/bio_analysis_results/for_eval/241210_j0251{version}_ct_random_{organelle}_eval_n{n_samples}_{gt_version}gt"
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    log = initialize_logging(f'rndm_{organelle}_coords_eval',
                             log_dir=f_name)
    log.info(f'Select random {organelle} coords from gt cells')
    log.info(f'GT version is {gt_version}')

    log.info(f'{n_samples} random samples are selected per cell type. Fragment class will not be evaluated')
    np.random.seed(42)

    log.info('Step 1/2: Load cellids and celltypes from groundtruth')
    cts_str = np.array(bio_params.ct_str(with_glia=True))
    #remove class fragments
    cts_str = cts_str[np.in1d(cts_str, 'FRAG') == False]
    axon_cts = bio_params.axon_cts()
    axon_str = [ct_dict[ct] for ct in axon_cts]
    glia_cts = bio_params.glia_cts()
    glia_str = [ct_dict[ct] for ct in glia_cts]
    if organelle == 'golgi':
        cts_str = cts_str[np.in1d(cts_str, axon_str) == False]
    num_cts = len(cts_str)
    celltype_gt = pd.read_csv(
        f"cajal/nvmescratch/projects/data/songbird/j0251/groundtruth/celltypes/j0251_celltype_gt_{gt_version}_j0251_72_seg_20210127_agglo2_IDs.csv",
        names=["cellids", "celltype"])
    celltype_gt = celltype_gt[np.in1d(celltype_gt['celltype'], cts_str)]
    cellids = np.array(celltype_gt['cellids'])
    ct_gt = np.array(celltype_gt['celltype'])
    assert(len(np.unique(ct_gt)) == num_cts)

    log.info(f'Step 2/2: Load {organelle} meshes and select random samples per celltype')
    rndm_org_coords = pd.DataFrame(columns = ['cellid', 'celltype', 'coord x', 'coord y', 'coord z', 'organelle'], index = range(num_cts * n_samples))
    rndm_org_coords['organelle'] = organelle
    for i, ct_str in enumerate(cts_str):
        #get organelle meshes from the cells of this cell type
        ct_df = celltype_gt[celltype_gt['celltype'] == ct_str]
        ct_ids = ct_df['cellids']
        log.info(f'{len(ct_ids)} were found for cell type {ct_str}')
        ct_org_vert_coords = []
        ct_org_cellids = []
        if organelle == 'single vesicle':
            # use single vesicle coordinates and load for all cells from celltype
            #use only for neuronal cell types
            if ct_str in axon_str or ct_str in glia_str:
                ct_ves_coords = np.load(f'{bio_params.file_locations}/{ct_str}_rep_coords.npy')
                ct_ves_map2ssvids = np.load(f'{bio_params.file_locations}/{ct_str}_mapping_ssv_ids.npy')
            else:
                ct_ves_coords = np.load(f'{bio_params.file_locations}/{ct_str}_rep_coords_fullcells.npy')
                ct_ves_map2ssvids = np.load(f'{bio_params.file_locations}/{ct_str}_mapping_ssv_ids_fullcells.npy')
            ct_ind = np.in1d(ct_ves_map2ssvids, ct_ids)
            ct_org_cellids = ct_ves_map2ssvids[ct_ind]
            ct_org_vert_coords = ct_ves_coords[ct_ind]
        else:
            for ct_id in ct_ids:
                if organelle == 'er':
                    #er is only one object per cell
                    org_obj = sd_org.get_segmentation_object(ct_id)
                    org_inds, org_verts, org_norm = org_obj.mesh
                    #get coordinates in voxel space to investigate in neuroglancer
                    org_verts = np.round(org_verts.reshape((-1, 3))/ [10, 10, 25])
                    org_cellid = np.zeros(len(org_verts)) + ct_id
                    ct_org_vert_coords.append(org_verts)
                    ct_org_cellids.append(org_cellid)
                else:
                    cell = SuperSegmentationObject(ct_id)
                    obj_organelles = cell.get_seg_objects(organelle)
                    for org_obj in obj_organelles:
                        org_inds, org_verts, org_norm = org_obj.mesh
                        org_verts = np.round(org_verts.reshape((-1, 3)) / [10, 10, 25])
                        org_cellid = np.zeros(len(org_verts)) + ct_id
                        ct_org_vert_coords.append(org_verts)
                        ct_org_cellids.append(org_cellid)
            ct_org_vert_coords = np.concatenate(ct_org_vert_coords)
            ct_org_cellids = np.concatenate(ct_org_cellids)
        rndm_inds = np.random.choice(range(len(ct_org_vert_coords)), n_samples, replace=False)
        rndm_coords_ct = ct_org_vert_coords[rndm_inds].astype(int)
        rndm_coords_cellids = ct_org_cellids[rndm_inds].astype(int)
        log.info(f'for celltype {ct_str}, rndm coordinates were selected from {len(np.unique(rndm_coords_cellids))} cellids.')
        rndm_org_coords.loc[i*n_samples: (i+1)*n_samples -1, 'celltype'] = ct_str
        rndm_org_coords.loc[i * n_samples: (i + 1) * n_samples - 1, 'cellid'] = rndm_coords_cellids
        rndm_org_coords.loc[i * n_samples: (i + 1) * n_samples - 1, 'coord x'] = rndm_coords_ct[:, 0]
        rndm_org_coords.loc[i * n_samples: (i + 1) * n_samples - 1, 'coord y'] = rndm_coords_ct[:, 1]
        rndm_org_coords.loc[i * n_samples: (i + 1) * n_samples - 1, 'coord z'] = rndm_coords_ct[:, 2]

    rndm_org_coords = shuffle(rndm_org_coords)
    rndm_org_coords.to_csv(f'{f_name}/random_{organelle}_coords.csv')
    log.info(f'{len(rndm_org_coords)} random coordinates were selected from {num_cts} celltypes.')
    log.info('Randomly selecting vesicles for evaluation done')