#script to visualise comparetment predictions of 3 random cells of each class

if __name__ == '__main__':
    import time
    from syconn.handler.config import initialize_logging
    from syconn import global_params
    import os as os
    import pandas as pd
    import numpy as np
    from tqdm import tqdm
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_params import Analysis_Params
    from syconn.mp.mp_utils import start_multiprocess_imap
    from sklearn.utils import shuffle
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_morph_helper import check_comp_lengths_ct, generate_colored_mesh_from_skel_data
    import time
    from syconn.handler.basics import load_pkl2obj


    #global_params.wd = "/ssdscratch/songbird/j0251/j0251_72_seg_20210127_agglo2"
    #global_params.wd = '/cajal/nvmescratch/projects/data/songbird/j0251/j0251_72_seg_20210127_agglo2_syn_20220811_celltypes_20230822'
    version = 'v6'
    analysis_params = Analysis_Params(version = version)
    global_params.wd = analysis_params.working_dir()
    ct_dict = analysis_params.ct_dict(with_glia=True)
    min_comp_len = 200
    #samples per ct
    rnd_samples = 3
    color_key = 'axoness_avg10000'
    k = 1
    f_name = f"cajal/scratch/users/arother/bio_analysis_results/for_eval/240812_j0251{version}_random_comp_val_mcl_%i_samples_%i_k%s" % (
        min_comp_len, rnd_samples, color_key)
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    log = initialize_logging('select random subset of cells to write mesh to kzip to visualise compartments',
                             log_dir=f_name + '/logs/')
    log.info(
        f"min_comp_len = %i, number of samples per ct = %i, key to color to = %s" % (
            min_comp_len, rnd_samples, color_key))
    log.info(f'k = {k} (closest skeleton nodes used for comp)')


    log.info(f'Iterate over celltypes to write out {rnd_samples} cells with compartments')
    cache_name = "/cajal/nvmescratch/users/arother/j0251v6_prep"
    num_cts = analysis_params.num_cts()
    ax_cts = analysis_params.axon_cts()
    cts_str = analysis_params.ct_str()
    known_mergers = analysis_params.load_known_mergers()
    pot_astros = analysis_params.load_potential_astros()
    np.random.seed(42)
    selected_ids = pd.DataFrame(columns = cts_str, index = range(rnd_samples))
    rnd_cellids_cts = []

    for ct in tqdm(range(num_cts)):
        # only get cells with min_comp_len, MSN with max_comp_len or axons with min ax_len
        ct_str = ct_dict[ct]
        cell_dict = analysis_params.load_cell_dict(ct)
        cellids = np.array(list(cell_dict.keys()))
        merger_inds = np.in1d(cellids, known_mergers) == False
        cellids = cellids[merger_inds]
        if ct in ax_cts:
            cellids_checked = check_comp_lengths_ct(cellids=cellids, fullcelldict=cell_dict,
                                                    min_comp_len=min_comp_len, axon_only=True,
                                                    max_path_len=None)
        else:
            if ct == 3:
                misclassified_asto_ids = analysis_params.load_potential_astros()
                astro_inds = np.in1d(cellids, misclassified_asto_ids) == False
                cellids = cellids[astro_inds]
            cellids = check_comp_lengths_ct(cellids=cellids, fullcelldict=cell_dict, min_comp_len=min_comp_len,
                                                axon_only=False, max_path_len=None)
        log.info("%i cells of celltype %s match criteria" % (len(cellids), ct_dict[ct]))
        #select cells randomly
        rnd_cellids = np.random.choice(a=cellids, size=rnd_samples, replace=False)
        selected_ids[ct_str] = rnd_cellids
        rnd_cellids_cts.append(rnd_cellids)

    selected_ids.to_csv(f'{f_name}/rnd_cellids.csv')
    rnd_cellids_cts = np.hstack(np.array(rnd_cellids_cts)).astype(int)

    log.info('Generate mesh from selected cellids')
    args = [[rnd_cellid, f_name, color_key, True, k, ct_dict] for rnd_cellid in rnd_cellids_cts]
    #generate mesh from cellids
    #global_params.wd = "cajal/nvmescratch/projects/data/songbird_tmp/j0251/j0251_72_seg_20210127_agglo2_syn_20220811"
    out = start_multiprocess_imap(generate_colored_mesh_from_skel_data, args)

    log.info(f'Generated colored meshes for {len(rnd_cellids_cts)} cells')


