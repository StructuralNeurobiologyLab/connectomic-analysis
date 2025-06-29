#similar to select_random_vesicles_for_eval
#select random er coordinates for eval
#have to get from the meshes as only one rep_coord per cell mapped


if __name__ == '__main__':
    import time
    from syconn.handler.config import initialize_logging
    from syconn import global_params
    from syconn.reps.segmentation import SegmentationDataset
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
    sd_er = SegmentationDataset('er', working_dir=global_params.config.working_dir)
    ct_dict = bio_params.ct_dict(with_glia = True)
    n_samples = 15
    gt_version = 'v7'
    color_key = 'TePkBr'
    f_name = f"cajal/scratch/users/arother/bio_analysis_results/for_eval/240925_j0251{version}_ct_random_er_eval_n{n_samples}_{gt_version}gt"
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    log = initialize_logging('select random subset of single vesicles for evaluation',
                             log_dir=f_name + '/logs/')
    log.info(f'Select random er coords from gt cells')
    log.info(f'GT version is {gt_version}')

    log.info(f'{n_samples} random samples are selected per cell type. Fragment class will not be evaluated')
    np.random.seed(42)

    log.info('Step 1/2: Load cellids and celltypes from groundtruth')
    cts_str = np.array(bio_params.ct_str(with_glia=True))
    #remove class fragments
    cts_str = cts_str[np.in1d(cts_str, 'FRAG') == False]
    num_cts = len(cts_str)
    celltype_gt = pd.read_csv(
        f"cajal/nvmescratch/projects/data/songbird/j0251/groundtruth/celltypes/j0251_celltype_gt_{gt_version}_j0251_72_seg_20210127_agglo2_IDs.csv",
        names=["cellids", "celltype"])
    celltype_gt = celltype_gt[np.in1d(celltype_gt['celltype'], cts_str)]
    cellids = np.array(celltype_gt['cellids'])
    ct_gt = np.array(celltype_gt['celltype'])
    assert(len(np.unique(ct_gt)) == num_cts)

    log.info('Step 2/2: Load ER meshes and select random samples per celltype')
    rndm_er_coords = pd.DataFrame(columns = ['cellid', 'celltype', 'coord x', 'coord y', 'coord z'], index = range(num_cts * n_samples))
    for i, ct in enumerate(range(num_cts)):
        #get ER meshes from the cells of this cell type
        ct_str = ct_dict[ct]
        ct_df = celltype_gt[celltype_gt['celltype'] == ct_str]
        ct_ids = ct_df['cellids']
        log.info(f'{len(ct_ids)} were found for cell type {ct_str}')
        ct_er_vert_coords = []
        ct_er_cellids = []
        for ct_id in ct_ids:
            er_obj = sd_er.get_segmentation_object(ct_id)
            er_inds, er_verts, er_norm = er_obj.mesh
            #get coordinates in voxel space to investigate in neuroglancer
            er_verts = np.round(er_verts.reshape((-1, 3))/ [10, 10, 25])
            er_cellid = np.zeros(len(er_verts)) + ct_id
            ct_er_vert_coords.append(er_verts)
            ct_er_cellids.append(er_cellid)
        ct_er_vert_coords = np.concatenate(ct_er_vert_coords)
        ct_er_cellids = np.concatenate(ct_er_cellids)
        rndm_inds = np.random.choice(range(len(ct_er_vert_coords)), n_samples, replace=False)
        rndm_coords_ct = ct_er_vert_coords[rndm_inds].astype(int)
        rndm_coords_cellids = ct_er_cellids[rndm_inds].astype(int)
        log.info(f'for celltype {ct_str}, rndm coordinates were selected from {len(np.unique(rndm_coords_cellids))} cellids.')
        rndm_er_coords.loc[i*n_samples: (i+1)*n_samples -1, 'celltype'] = ct_str
        rndm_er_coords.loc[i * n_samples: (i + 1) * n_samples - 1, 'cellid'] = rndm_coords_cellids
        rndm_er_coords.loc[i * n_samples: (i + 1) * n_samples - 1, 'coord x'] = rndm_coords_ct[:, 0]
        rndm_er_coords.loc[i * n_samples: (i + 1) * n_samples - 1, 'coord y'] = rndm_coords_ct[:, 1]
        rndm_er_coords.loc[i * n_samples: (i + 1) * n_samples - 1, 'coord z'] = rndm_coords_ct[:, 2]

    rndm_er_coords = shuffle(rndm_er_coords)
    rndm_er_coords.to_csv(f'{f_name}/random_er_coords.csv')
    log.info(f'{len(rndm_er_coords)} random coordinates were selected from {num_cts} celltypes.')
    log.info('Randomly selecting vesicles for evaluation done')