#script to visualize synapse probabilities on meshes
#similar to rnd_mesh_comp_visualisations
#use also same cells

if __name__ == '__main__':
    from syconn.handler.config import initialize_logging
    from syconn import global_params
    import os as os
    import pandas as pd
    import numpy as np
    from tqdm import tqdm
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_params import Analysis_Params
    from syconn.mp.mp_utils import start_multiprocess_imap
    from syconn.reps.segmentation import SegmentationDataset
    from sklearn.utils import shuffle
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_morph_helper import check_comp_lengths_ct, generate_colored_mesh_synprob_data
    from syconn.handler.basics import load_pkl2obj
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_conn_helper import filter_synapse_caches_for_ct
    import seaborn as sns
    import matplotlib.pyplot as plt
    import matplotlib.colors as co

    version = 'v6'
    analysis_params = Analysis_Params(version = version)
    global_params.wd = analysis_params.working_dir()
    ct_dict = analysis_params.ct_dict(with_glia= False)
    min_comp_len = 200
    #samples per ct
    rnd_samples = 3
    color_key = 'axoness_avg10000'
    min_syn_size = 0.1
    use_selected_ids = True
    f_name = f"cajal/scratch/users/arother/bio_analysis_results/for_eval/241016_j0251{version}_synprob_old_cts_mesh_visualization_mcl_%i_samples_%i_k%s_ms_%.1f" % (
        min_comp_len, rnd_samples, color_key, min_syn_size)
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    log = initialize_logging('synprob_mesh_visualisation',
                             log_dir=f_name + '/logs/')
    log.info(
        f"min_comp_len = %i, number of samples per ct = %i, key to color to = %s, minimum synapse size = %.1f" % (
            min_comp_len, rnd_samples, color_key, min_syn_size))

    log.info(f'Iterate over celltypes to write out {rnd_samples} cells with compartments')
    num_cts = analysis_params.num_cts()
    ax_cts = analysis_params.axon_cts()
    cts_str = analysis_params.ct_str()

    if use_selected_ids:
        selected_id_path = 'cajal/scratch/users/arother/bio_analysis_results/for_eval/230412_j0251v4_synprob_mesh_visualization_mcl_200_samples_3_kaxoness_avg10000_ms_0.1/' \
                           'rnd_cellids_for_comparison.csv'
        log.info(f' Load cellids previously selected from {selected_id_path}')
        cellid_df = pd.read_csv(selected_id_path)
        cellid_df = cellid_df[['cellid', 'celltype']]
        cellid_df = cellid_df.dropna()
        cellid_df.to_csv(f'{f_name}/prev_sel_cellids.csv')
        rnd_cellids_cts = np.array(cellid_df['cellid']).astype(int)

    else:
        selected_ids = pd.DataFrame(columns=cts_str, index=range(rnd_samples))
        cache_name = "/cajal/nvmescratch/users/arother/j0251v4_prep"
        known_mergers = analysis_params.load_known_mergers()
        pot_astros = analysis_params.load_potential_astros()
        np.random.seed(42)
        rnd_cellids_cts = []

        for ct in tqdm(range(num_cts)):
            # only get cells with min_comp_len, MSN with max_comp_len or axons with min ax_len
            ct_str = ct_dict[ct]
            if ct in ax_cts:
                cell_dict = analysis_params.load_cell_dict(ct)
                cellids = np.array(list(cell_dict.keys()))
                merger_inds = np.in1d(cellids, known_mergers) == False
                cellids = cellids[merger_inds]
                cellids = check_comp_lengths_ct(cellids=cellids, fullcelldict=cell_dict, min_comp_len=min_comp_len,
                                                axon_only=True, max_path_len=None)
            else:
                cell_dict = analysis_params.load_cell_dict(ct)
                cellids = load_pkl2obj(
                    f"{cache_name}/full_%.3s_arr.pkl" % ct_dict[ct])
                merger_inds = np.in1d(cellids, known_mergers) == False
                cellids = cellids[merger_inds]
                if ct == 2:
                    misclassified_asto_ids = load_pkl2obj(f'{cache_name}/pot_astro_ids.pkl')
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
        rnd_cellids_cts = np.hstack(np.array(rnd_cellids_cts))

    log.info('Prefilter synapse information')
    sd_synssv = SegmentationDataset('syn_ssv', working_dir = global_params.wd)
    pre_cts = np.arange(num_cts)
    post_cts = pre_cts[np.in1d(pre_cts, ax_cts) == False]
    #use filtering for minimal synapse size and pre, postcts, only axo-dendritic/axo-somatic synapses but not for synapse probability
    syn_cts, syn_ids, syn_axs, syn_ssv_partners, syn_sizes, syn_spiness, syn_rep_coord, syn_prob = filter_synapse_caches_for_ct(sd_synssv = sd_synssv,
                                                                                                        pre_cts = pre_cts,
                                                                                                        post_cts=post_cts,
                                                                                                        syn_prob_thresh=None,
                                                                                                        min_syn_size=min_syn_size,
                                                                                                        axo_den_so=True, return_syn_prob=True)

    log.info('Generate mesh from selected cellids')
    cats = [0.0, 0.2, 0.4, 0.6, 0.8]
    colors_hex = ['#D62246','#912043','#232121','#0E7C7B','#17BEBB']
    colors_rgba = co.to_rgba_array(colors_hex)
    colors_rgba_int = colors_rgba * 255
    col_lookup = {cats[i]: colors_rgba_int[i] for i in range(len(cats))}
    #nan_col = '#707070'
    #nan_col_rgba_int = co.to_rgba_array(nan_col) * 255
    #col_lookup[-1.0] = nan_col_rgba_int

    #visualize color palette with categories
    sns.palplot(colors_rgba)
    ax = plt.gca()
    for i, key in enumerate(col_lookup.keys()):
        ax.text(i, 0, key)
    plt.savefig(f'{f_name}/syn_prob_color_palette.png')
    plt.close()
    cell_input = [[rnd_cellid, f_name, syn_ssv_partners, syn_rep_coord, syn_prob, col_lookup] for rnd_cellid in rnd_cellids_cts]
    #generate mesh from cellids
    _ = start_multiprocess_imap(generate_colored_mesh_synprob_data, cell_input)

    log.info(f'Generated colored meshes for {len(rnd_cellids_cts)} cells')
