#connectivity fraction per ct but with ngf subpopulations
#modify code from connectivity fraction per ct

if __name__ == '__main__':
    from analysis_morph_helper import check_comp_lengths_ct
    from analysis_conn_helper import filter_synapse_caches_for_ct, get_number_sum_size_synapses, filter_synapse_caches_general
    from result_helper import ConnMatrix
    from analysis_colors import CelltypeColors
    from analysis_params import Analysis_Params
    import time
    from syconn.handler.config import initialize_logging
    from syconn import global_params
    from syconn.reps.segmentation import SegmentationDataset
    from syconn.reps.super_segmentation import SuperSegmentationDataset
    import os as os
    import pandas as pd
    from syconn.handler.basics import write_obj2pkl, load_pkl2obj
    import numpy as np
    from tqdm import tqdm
    import seaborn as sns
    import matplotlib.pyplot as plt

    global_params.wd = "/cajal/nvmescratch/projects/data/songbird_tmp/j0251/j0251_72_seg_20210127_agglo2_syn_20220811"
    #global_params.wd = 'cajal/nvmescratch/projects/from_ssdscratch/songbird/j0251/j0251_72_seg_20210127_agglo2'
    sd_synssv = SegmentationDataset('syn_ssv', working_dir=global_params.config.working_dir)
    ssd = SuperSegmentationDataset(working_dir=global_params.config.working_dir)
    start = time.time()
    analysis_params = Analysis_Params(working_dir=global_params.wd, version='v5')
    ct_dict = analysis_params.ct_dict(with_glia=False)
    celltype_key = analysis_params.celltype_key()
    min_comp_len_ax = 50
    min_comp_len_cells = 200
    syn_prob = 0.6
    min_syn_size = 0.1
    exclude_known_mergers = True
    cls = CelltypeColors()
    #color keys: 'BlRdGy', 'MudGrays', 'BlGrTe','TePkBr', 'BlYw', 'STNGP', 'NGF'}
    color_key = 'TePkBrNGF'
    plot_connmatrix_only = False
    fontsize = 12
    annot = True
    f_name = "cajal/scratch/users/arother/bio_analysis_results/general/230920_j0251v5_cts_percentages_ngf_subgroups_mcl_%i_ax%i_synprob_%.2f_%s_annot_bw_fs_%i" % (
    min_comp_len_cells, min_comp_len_ax, syn_prob, color_key, fontsize)
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    save_svg = True
    log = initialize_logging('Celltypes input output percentages', log_dir=f_name + '/logs/')
    log.info(
        "min_comp_len = %i for full cells, min_comp_len = %i for axons, syn_prob = %.1f, min_syn_size = %.1f, known mergers excluded = %s, colors = %s" % (
        min_comp_len_cells, min_comp_len_ax, syn_prob, min_syn_size, exclude_known_mergers, color_key))
    log.info('Instead of ngf, ngf subgroups will be used as individual celltypes')
    ct_dict[10] = 'TP1'
    ct_dict[11] = 'TP2'

    #this script should iterate over all celltypes
    axon_cts = [1, 3, 4]
    log.info("Step 1/3: Load cell dicts and get suitable cellids")
    if exclude_known_mergers:
        known_mergers = analysis_params.load_known_mergers()
    #To Do: also exlclude MSNs from list
    celltypes = np.array([ct_dict[ct] for ct in ct_dict])
    num_cts = len(celltypes)
    full_cell_dicts = {}
    suitable_ids_dict = {}
    all_suitable_ids = []
    cts_numbers_perct = pd.DataFrame(columns=['total number of cells', 'number of suitable cells', 'percentage of suitable cells'], index=celltypes)
    for ct in tqdm(range(num_cts)):
        ct_str = ct_dict[ct]
        if ct in axon_cts:
            cell_dict = analysis_params.load_cell_dict(ct)
            #get ids with min compartment length
            cellids = np.array(list(cell_dict.keys()))
            merger_inds = np.in1d(cellids, known_mergers) == False
            cellids = cellids[merger_inds]
            cellids_checked = check_comp_lengths_ct(cellids=cellids, fullcelldict=cell_dict, min_comp_len=min_comp_len_ax, axon_only=True,
                              max_path_len=None)
            cts_numbers_perct.loc[ct_str, 'total number of cells'] = len(cellids)
        else:
            if ct < 10:
                cell_dict = analysis_params.load_cell_dict(ct)
                cellids = np.array(list(cell_dict.keys()))
            else:
                cell_dict = analysis_params.load_cell_dict(10)
                if ct == 10:
                    cellids = analysis_params.load_ngf_subids(type = 1)
                else:
                    cellids = analysis_params.load_ngf_subids(type=2)
            if exclude_known_mergers:
                merger_inds = np.in1d(cellids, known_mergers) == False
                cellids = cellids[merger_inds]
            if ct == 2:
                misclassified_asto_ids = analysis_params.load_potential_astros()
                astro_inds = np.in1d(cellids, misclassified_asto_ids) == False
                cellids = cellids[astro_inds]
            cellids_checked = check_comp_lengths_ct(cellids=cellids, fullcelldict=cell_dict, min_comp_len=min_comp_len_cells,
                                                axon_only=False,
                                                max_path_len=None)

        full_cell_dicts[ct] = cell_dict
        suitable_ids_dict[ct] = cellids_checked
        cts_numbers_perct.loc[ct_str, 'number of suitable cells'] = len(cellids_checked)
        all_suitable_ids.append(cellids_checked)

    all_suitable_ids = np.concatenate(all_suitable_ids)
    write_obj2pkl("%s/suitable_ids_allct.pkl" % f_name, suitable_ids_dict)
    cts_numbers_perct.to_csv("%s/numbers_perct.csv" % f_name)
    time_stamps = [time.time()]
    step_idents = ['Suitable cellids loaded']

    log.info("Step 2/3: Get synapse number and sum of synapse size fractions for each celltype")
    synapse_dict_perct = {i: {} for i in range(num_cts)}
    synapse_pd_perct = pd.DataFrame(index=celltypes)
    non_ax_celltypes = celltypes[np.in1d(np.arange(0, num_cts), axon_cts) == False]
    ct_colours = cls.colors[color_key]
    ct_palette = cls.ct_palette_add_groups(color_key, ct = 10, add_groups=['TP1', 'TP2'], num = False)
    #index = postsynapse, column is post-synapse
    outgoing_synapse_matrix_synnumbers_rel = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)
    outgoing_synapse_matrix_synsizes_rel = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)
    outgoing_synapse_matrix_synnumbers_abs = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)
    outgoing_synapse_matrix_synsizes_abs_med = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)
    incoming_synapse_matrix_synnumbers_rel = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)
    incoming_synapse_matrix_synsizes_rel = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)
    incoming_synapse_matrix_synnumbers_abs = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)
    incoming_synapse_matrix_synsizes_abs_med = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)
    outgoing_synapse_matrix_synsizes_abs_sum = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)
    incoming_synapse_matrix_synsizes_abs_sum = pd.DataFrame(columns=non_ax_celltypes, index=celltypes)

    # prefilter synapses for synapse prob thresh and min syn size
    '''
    m_cts, m_ids, m_axs, m_ssv_partners, m_sizes, m_spiness, m_rep_coord, syn_prob = filter_synapse_caches_general(
        sd_synssv,
        syn_prob_thresh=syn_prob,
        min_syn_size=min_syn_size)
    '''
    m_cts, m_axs, m_ssv_partners, m_sizes, m_rep_coord, syn_prob = filter_synapse_caches_general(
        sd_synssv,
        syn_prob_thresh=syn_prob,
        min_syn_size=min_syn_size)
    #as ngf subgroups are only full ids: filter out all cells that are not full
    #filter out all cells that are not in suitable_ids_dict
    suit_ct_inds = np.all(np.in1d(m_ssv_partners, all_suitable_ids).reshape(len(m_ssv_partners), 2), axis=1)
    m_cts = m_cts[suit_ct_inds]
    #m_ids = m_ids[suit_ct_inds]
    m_ssv_partners = m_ssv_partners[suit_ct_inds]
    m_sizes = m_sizes[suit_ct_inds]
    m_axs = m_axs[suit_ct_inds]
    #m_spiness = m_spiness[suit_ct_inds]
    m_rep_coord = m_rep_coord[suit_ct_inds]
    syn_prob = syn_prob[suit_ct_inds]
    #change m_cts from all cells from ngf type 2 to 11
    type2_inds = np.in1d(m_ssv_partners, suitable_ids_dict[11]).reshape(len(m_ssv_partners), 2)
    type2_inds_where = np.where(type2_inds == True)
    m_cts[type2_inds_where] = 11
    #synapse_cache = [m_cts, m_ids, m_axs, m_ssv_partners, m_sizes, m_spiness, m_rep_coord, syn_prob]
    synapse_cache = [m_cts, m_axs, m_ssv_partners, m_sizes, m_rep_coord, syn_prob]

    for ct in tqdm(range(num_cts)):
        ct_str = ct_dict[ct]
        #get synapses where ct is involved with syn_prob, min_syn_size
        '''
        m_cts, m_ids, m_axs, m_ssv_partners, m_sizes, m_spiness, m_rep_coord = filter_synapse_caches_for_ct(pre_cts=[ct],
                                                                                                                post_cts=None,
                                                                                                                syn_prob_thresh=None,
                                                                                                                min_syn_size=None,
                                                                                                                axo_den_so=True, synapses_caches=synapse_cache)
        '''
        m_cts, m_axs, m_ssv_partners, m_sizes, m_rep_coord = filter_synapse_caches_for_ct(
            pre_cts=[ct],
            post_cts=None,
            syn_prob_thresh=None,
            min_syn_size=None,
            axo_den_so=True, synapses_caches=synapse_cache)
        #seperate in incoming and outgoing synapses
        #incoming synapses
        if ct not in axon_cts:
            #incoming synapses of suitable cells of ct only
            #get only synapses that are with other suitable ids from every cts
            in_sizes, in_ssv_partners, in_axs, in_cts, unique_in_ssvs, in_syn_sizes, in_syn_numbers = get_number_sum_size_synapses(
                syn_sizes=m_sizes,
                syn_ssv_partners=m_ssv_partners,
                syn_axs=m_axs, syn_cts=m_cts,
                ct=ct, cellids=suitable_ids_dict[ct],
                filter_ax=[0,2],
                filter_ids=all_suitable_ids, return_syn_arrays=True)
            sorted_full_in_inds = np.argsort(unique_in_ssvs)
            sorted_full_in_ssvs = unique_in_ssvs[sorted_full_in_inds]
            sorted_full_in_numbers = in_syn_numbers[sorted_full_in_inds]
            sorted_full_in_sizes = in_syn_sizes[sorted_full_in_inds]
            synapse_dict_perct[ct]['in full cellids'] = sorted_full_in_ssvs
            synapse_dict_perct[ct]['incoming full cell synapse number'] = sorted_full_in_numbers
            synapse_dict_perct[ct]['incoming full cell synapse sum size'] = sorted_full_in_sizes
            synapse_pd_perct.loc[ct_str, 'median incoming full cell synapse number'] = np.median(sorted_full_in_numbers)
            synapse_pd_perct.loc[ct_str, 'median incoming full cell synapse sum size'] = np.median(sorted_full_in_sizes)
        #outgoing synapses
        # get only synapses that are with other suitable ids from every cts
        out_sizes, out_ssv_partners, out_axs, out_cts, unique_out_ssvs, out_syn_sizes, out_syn_numbers = get_number_sum_size_synapses(
            syn_sizes=m_sizes,
            syn_ssv_partners=m_ssv_partners,
            syn_axs=m_axs, syn_cts=m_cts,
            ct=ct, cellids=suitable_ids_dict[ct],
            filter_ax=[1],
            filter_ids=all_suitable_ids, return_syn_arrays=True)
        sorted_full_out_inds = np.argsort(unique_out_ssvs)
        sorted_full_out_ssvs = unique_out_ssvs[sorted_full_out_inds]
        sorted_full_out_numbers = out_syn_numbers[sorted_full_out_inds]
        sorted_full_out_sizes = out_syn_sizes[sorted_full_out_inds]
        synapse_dict_perct[ct]['out full cellids'] = sorted_full_out_ssvs
        synapse_dict_perct[ct]['outgoing full cell synapse number'] = sorted_full_out_numbers
        synapse_dict_perct[ct]['outgoing full cell synapse sum size'] = sorted_full_out_sizes
        synapse_pd_perct.loc[ct_str, 'median outgoing full cell synapse number'] = np.median(sorted_full_out_numbers)
        synapse_pd_perct.loc[ct_str, 'median outgoing full cell synapse sum size'] = np.median(sorted_full_out_sizes)
        #get sum size and sum of synapses for each celltype seperate (only full cells)
        for other_ct in range(num_cts):
            other_ct_str = ct_dict[other_ct]
            if ct not in axon_cts:
                #incoming synapses
                if other_ct == ct:
                    unique_in_ssvs, in_syn_sizes, in_syn_numbers = get_number_sum_size_synapses(
                        syn_sizes=in_sizes, syn_ssv_partners=in_ssv_partners,
                        syn_axs=in_axs, syn_cts=in_cts, ct=ct, cellids=suitable_ids_dict[ct],
                        filter_ax=[0,2], filter_ids=suitable_ids_dict[ct], return_syn_arrays=False,
                        filter_pre_ids=None, filter_post_ids=None)
                else:
                    unique_in_ssvs, in_syn_sizes, in_syn_numbers = get_number_sum_size_synapses(
                            syn_sizes=in_sizes, syn_ssv_partners=in_ssv_partners,
                            syn_axs=in_axs, syn_cts=in_cts, ct=ct, cellids=suitable_ids_dict[ct],
                            filter_ax=None, filter_ids=None, return_syn_arrays=False,
                            filter_pre_ids=suitable_ids_dict[other_ct], filter_post_ids=suitable_ids_dict[ct])
                #add zeros for cells that have no synapses to this celltype, re-order arrays to full ssv ids
                #sort array for this
                sorted_in_ssv_ind = np.argsort(unique_in_ssvs)
                sorted_in_ssvs = unique_in_ssvs[sorted_in_ssv_ind]
                sorted_in_numbers = in_syn_numbers[sorted_in_ssv_ind]
                sorted_in_sizes = in_syn_sizes[sorted_in_ssv_ind]
                full_inds = np.in1d(sorted_full_in_ssvs, sorted_in_ssvs)
                filled_in_syn_numbers = np.zeros(len(sorted_full_in_ssvs))
                filled_in_syn_sizes = np.zeros(len(sorted_full_in_ssvs))
                filled_in_syn_numbers[full_inds == True] = sorted_in_numbers
                filled_in_syn_sizes[full_inds == True] = sorted_in_sizes
                synapse_dict_perct[ct][f'incoming synapse ids with {other_ct_str}'] = sorted_full_in_ssvs
                synapse_dict_perct[ct][f'incoming synapse number from {other_ct_str}'] = filled_in_syn_numbers
                synapse_dict_perct[ct][f'incoming synapse sum size from {other_ct_str}'] = filled_in_syn_sizes
                # column is pre, index = postsynapse
                incoming_synapse_matrix_synnumbers_abs.loc[ct_dict[other_ct], ct_dict[ct]] = np.median(filled_in_syn_numbers)
                incoming_synapse_matrix_synsizes_abs_med.loc[ct_dict[other_ct], ct_dict[ct]] = np.median(filled_in_syn_sizes)
                incoming_synapse_matrix_synsizes_abs_sum.loc[ct_dict[other_ct], ct_dict[ct]] = np.sum(
                    filled_in_syn_sizes)
                perc_syn_numbers = 100 * filled_in_syn_numbers / sorted_full_in_numbers
                perc_syn_sizes = 100 * filled_in_syn_sizes/ sorted_full_in_sizes
                synapse_dict_perct[ct][f'incoming synapse number percentage of {other_ct_str}'] = perc_syn_numbers
                synapse_dict_perct[ct][f'incoming synapse sum size percentage of {other_ct_str}'] = perc_syn_sizes
            #outgoing
            if other_ct in axon_cts:
                continue
            if other_ct == ct:
                unique_out_ssvs, out_syn_sizes, out_syn_numbers = get_number_sum_size_synapses(
                    syn_sizes=out_sizes, syn_ssv_partners=out_ssv_partners,
                    syn_axs=out_axs, syn_cts=out_cts, ct=ct, cellids=suitable_ids_dict[ct],
                    filter_ax=[1], filter_ids=suitable_ids_dict[ct], return_syn_arrays=False,
                    filter_pre_ids=None, filter_post_ids=None)
            else:
                unique_out_ssvs, out_syn_sizes, out_syn_numbers = get_number_sum_size_synapses(
                    syn_sizes=out_sizes, syn_ssv_partners=out_ssv_partners,
                    syn_axs=out_axs, syn_cts=out_cts, ct=ct, cellids=suitable_ids_dict[ct],
                    filter_ax=None, filter_ids=None, return_syn_arrays=False,
                    filter_pre_ids=suitable_ids_dict[ct], filter_post_ids=suitable_ids_dict[other_ct])
            sorted_out_ssv_ind = np.argsort(unique_out_ssvs)
            sorted_out_ssvs = unique_out_ssvs[sorted_out_ssv_ind]
            sorted_out_numbers = out_syn_numbers[sorted_out_ssv_ind]
            sorted_out_sizes = out_syn_sizes[sorted_out_ssv_ind]
            full_inds = np.in1d(sorted_full_out_ssvs, sorted_out_ssvs)
            filled_out_syn_numbers = np.zeros(len(sorted_full_out_ssvs))
            filled_out_syn_sizes = np.zeros(len(sorted_full_out_ssvs))
            filled_out_syn_numbers[full_inds == True] = sorted_out_numbers
            filled_out_syn_sizes[full_inds == True] = sorted_out_sizes
            synapse_dict_perct[ct][f'outgoing synapse ids with {other_ct_str}'] = sorted_full_out_ssvs
            synapse_dict_perct[ct][f'outgoing synapse number to {other_ct_str}'] = filled_out_syn_numbers
            synapse_dict_perct[ct][f'outgoing synapse sum size to {other_ct_str}'] = filled_out_syn_sizes
            # column is pre, index = postsynapse
            outgoing_synapse_matrix_synnumbers_abs.loc[ct_dict[ct], ct_dict[other_ct]] = np.median(filled_out_syn_numbers)
            outgoing_synapse_matrix_synsizes_abs_med.loc[ct_dict[ct], ct_dict[other_ct]] = np.median(filled_out_syn_sizes)
            outgoing_synapse_matrix_synsizes_abs_sum.loc[ct_dict[ct], ct_dict[other_ct]] = np.sum(
                filled_out_syn_sizes)
            perc_syn_numbers = 100 * filled_out_syn_numbers / sorted_full_out_numbers
            perc_syn_sizes = 100 * filled_out_syn_sizes / sorted_full_out_sizes
            synapse_dict_perct[ct][f'outgoing synapse number percentage of {other_ct_str}'] = perc_syn_numbers
            synapse_dict_perct[ct][f'outgoing synapse sum size percentage of {other_ct_str}'] = perc_syn_sizes
        # make plots per celltype, pie chart, violinplot
        if not plot_connmatrix_only:
            synapse_dict_ct = synapse_dict_perct[ct]
            f_name_ct = f'{f_name}/{ct_str}'
            if not os.path.exists(f_name_ct):
                os.mkdir(f_name_ct)
            for key in synapse_dict_ct:
                if 'ids' in key or 'full cell' in key or 'total' in key:
                    continue
                if ct_dict[0] in key:
                    key_name = key[:-3]
                    key_name_gen = key_name[:-6]
                    if 'incoming' in key:
                        plt_celltypes = celltypes
                    else:
                        plt_celltypes = non_ax_celltypes
                    lengths = [len(synapse_dict_ct[key_name + c]) for c in plt_celltypes]
                    max_length = np.max(lengths)
                    result_df = pd.DataFrame(columns=plt_celltypes, index=range(max_length))
                    for i, c in enumerate(plt_celltypes):
                        result_df.loc[0:lengths[i] - 1, c] = synapse_dict_ct[key_name + c]
                    #fill up with zeros so that each cell that makes at least one synapse with another suitable cell is included in analysis
                    result_df = result_df.fillna(0)
                    if 'percentage' in key:
                        ylabel = '%'
                    else:
                        if 'number' in key:
                            ylabel = 'synapse number'
                        else:
                            ylabel = 'sum of synapse size [µm²]'
                    sns.stripplot(data=result_df, palette='dark:black', alpha=0.2,
                                  dodge=True, size=2)
                    sns.violinplot(data=result_df, inner="box",
                                        palette=ct_palette)
                    plt.title(key_name_gen + ' of ' + ct_str)
                    plt.ylabel(ylabel)
                    if 'percentage' in key:
                        plt.ylim(0, 100)
                    plt.xticks(fontsize=fontsize)
                    plt.yticks(fontsize=fontsize)
                    plt.savefig('%s/%s_%s_violin.png' % (f_name_ct, key_name_gen, ct_str))
                    if save_svg:
                        plt.savefig('%s/%s_%s_violin.svg' % (f_name_ct, key_name_gen, ct_str))
                    plt.close()
                    sns.boxplot(data=result_df, palette=ct_palette)
                    plt.title(key_name_gen + ' of ' + ct_str)
                    plt.ylabel(ylabel)
                    plt.xticks(fontsize=fontsize)
                    plt.yticks(fontsize=fontsize)
                    if 'percentage' in key:
                        plt.ylim(0, 100)
                    plt.savefig('%s/%s_%s_box.png' % (f_name_ct, key_name_gen, ct_str))
                    if save_svg:
                        plt.savefig('%s/%s_%s_box.svg' % (f_name_ct, key_name_gen, ct_str))
                    plt.close()
                    #show standard deviation as error bar
                    sns.barplot(data = result_df, palette=ct_palette, errorbar="sd")
                    plt.title(key_name_gen + ' of ' + ct_str)
                    plt.ylabel(ylabel)
                    plt.xticks(fontsize=fontsize)
                    plt.yticks(fontsize=fontsize)
                    if 'percentage' in key:
                        plt.ylim(0, 100)
                    plt.savefig('%s/%s_%s_bar.png' % (f_name_ct, key_name_gen, ct_str))
                    if save_svg:
                        plt.savefig('%s/%s_%s_bar.svg' % (f_name_ct, key_name_gen, ct_str))
                    plt.close()
                    median_results = np.median(result_df, axis=0)
                    if 'percentage' in key:
                        plt.pie(median_results, labels = plt_celltypes, autopct='%.2f%%', colors=ct_colours)
                        plt.title(key_name_gen + ' of ' + ct_str + ', median values')
                        plt.savefig('%s/%s_%s_pie.png' % (f_name_ct, key_name_gen, ct_str))
                        plt.close()

    #save results as pkl and .csv
    write_obj2pkl('%s/synapse_dict_per_ct.pkl' % f_name, synapse_dict_perct)
    incoming_synapse_matrix_synnumbers_abs.to_csv('%s/incoming_syn_number_matrix_abs.csv' % f_name)
    incoming_synapse_matrix_synsizes_abs_med.to_csv('%s/incoming_syn_sizes_matrix_abs_med.csv' % f_name)
    incoming_synapse_matrix_synsizes_abs_sum.to_csv('%s/incoming_syn_sizes_matrix_abs_sum.csv' % f_name)
    outgoing_synapse_matrix_synnumbers_abs.to_csv('%s/outgoing_syn_number_matrix_abs.csv' % f_name)
    outgoing_synapse_matrix_synsizes_abs_med.to_csv('%s/outgoing_syn_sizes_matrix_abs_med.csv' % f_name)
    outgoing_synapse_matrix_synsizes_abs_sum.to_csv('%s/outgoing_syn_sizes_matrix_abs_sum.csv' % f_name)
    #create one matrix for incoming and outgoing each, which is sum size of synapses globalised to the dataset
    #get total sum of synapses and divide by that
    sum_incoming = np.sum(incoming_synapse_matrix_synsizes_abs_sum.sum())
    sum_outgoing = np.sum(outgoing_synapse_matrix_synsizes_abs_sum.sum())
    assert(sum_outgoing == sum_incoming)
    incoming_synapse_matrix_synsizes_abs_sum_dn = 100 * incoming_synapse_matrix_synsizes_abs_sum/ sum_incoming
    incoming_synapse_matrix_synsizes_rel = incoming_synapse_matrix_synsizes_abs_sum * 100 / incoming_synapse_matrix_synsizes_abs_sum.sum()
    incoming_synapse_matrix_synnumbers_rel = incoming_synapse_matrix_synnumbers_abs * 100 / incoming_synapse_matrix_synnumbers_abs.sum()
    outgoing_synapse_matrix_synsizes_abs_sum_dn = 100 * outgoing_synapse_matrix_synsizes_abs_sum / sum_outgoing
    outgoing_synapse_matrix_synsizes_rel = np.transpose(outgoing_synapse_matrix_synsizes_abs_sum.T * 100 / outgoing_synapse_matrix_synsizes_abs_sum.sum(axis = 1))
    outgoing_synapse_matrix_synnumbers_rel = np.transpose(outgoing_synapse_matrix_synnumbers_abs.T * 100 / outgoing_synapse_matrix_synnumbers_abs.sum(axis = 1))
    incoming_synapse_matrix_synsizes_abs_sum_dn.to_csv('%s/incoming_syn_sizes_matrix_abs_sum_dataset_norm.csv' % f_name)
    outgoing_synapse_matrix_synsizes_abs_sum_dn.to_csv('%s/outgoing_syn_sizes_matrix_abs_sum_datatset_norm.csv' % f_name)
    outgoing_synapse_matrix_synnumbers_rel.to_csv('%s/outgoing_syn_number_matrix_rel.csv' % f_name)
    outgoing_synapse_matrix_synsizes_rel.to_csv('%s/outgoing_syn_sizes_matrix_rel.csv' % f_name)
    incoming_synapse_matrix_synnumbers_rel.to_csv('%s/incoming_syn_number_matrix_rel.csv' % f_name)
    incoming_synapse_matrix_synsizes_rel.to_csv('%s/incoming_syn_sizes_matrix_rel.csv' % f_name)
    log.info("Created Matrix with median values for cellids, presynapse is index, post is columns")

    log.info('Step 3/3 Plot results')
    # column is pre, index = postsynapse
    #cmap_heatmap = sns.color_palette('crest', as_cmap=True)
    cmap_heatmap = sns.light_palette('black', as_cmap=True)
    inc_numbers_abs = ConnMatrix(data = incoming_synapse_matrix_synnumbers_abs.astype(float), title = 'Numbers of incoming synapses', filename = f_name, cmap = cmap_heatmap)
    inc_numbers_abs.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    inc_numbers_rel = ConnMatrix(data = incoming_synapse_matrix_synnumbers_rel.astype(float), title = 'Percentage of incoming synapse numbers', filename = f_name, cmap = cmap_heatmap)
    inc_numbers_rel.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    inc_sizes_abs_med = ConnMatrix(data = incoming_synapse_matrix_synsizes_abs_med.astype(float), title = 'Summed sizes of incoming synapses per cell', filename = f_name, cmap = cmap_heatmap)
    inc_sizes_abs_med.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    inc_sizes_abs_sum = ConnMatrix(data=incoming_synapse_matrix_synsizes_abs_sum.astype(float),
                                   title='Summed sizes of incoming synapses', filename=f_name,
                                   cmap=cmap_heatmap)
    inc_sizes_abs_sum.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    inc_sizes_rel = ConnMatrix(data = incoming_synapse_matrix_synsizes_rel.astype(float), title = 'Percentage of incoming synapses summed sizes', filename = f_name, cmap = cmap_heatmap)
    inc_sizes_rel.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    out_numbers_abs = ConnMatrix(data=outgoing_synapse_matrix_synnumbers_abs.astype(float), title='Numbers of outgoing synapses',
                                 filename=f_name, cmap = cmap_heatmap)
    out_numbers_abs.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    out_numbers_rel = ConnMatrix(data=outgoing_synapse_matrix_synnumbers_rel.astype(float),
                                 title='Percentage of outgoing synapse numbers', filename=f_name, cmap = cmap_heatmap)
    out_numbers_rel.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    out_sizes_abs_med = ConnMatrix(data=outgoing_synapse_matrix_synsizes_abs_med.astype(float), title='Summed sizes of outgoing synapses per cell',
                               filename=f_name, cmap = cmap_heatmap)
    out_sizes_abs_med.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    out_sizes_abs_sum = ConnMatrix(data=outgoing_synapse_matrix_synsizes_abs_sum.astype(float),
                                   title='Summed sizes of outgoing synapses',
                                   filename=f_name, cmap=cmap_heatmap)
    out_sizes_abs_sum.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    out_sizes_rel = ConnMatrix(data=outgoing_synapse_matrix_synsizes_rel.astype(float),
                               title='Percentage of outgoing synapses summed sizes', filename=f_name, cmap = cmap_heatmap)
    out_sizes_rel.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    in_sizes_abs_sum_dn = ConnMatrix(data=incoming_synapse_matrix_synsizes_abs_sum_dn.astype(float),
                                   title='Summed sizes of incoming synapses globally normalised',
                                   filename=f_name, cmap=cmap_heatmap)
    in_sizes_abs_sum_dn.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)
    out_sizes_abs_sum_dn = ConnMatrix(data=outgoing_synapse_matrix_synsizes_abs_sum_dn.astype(float),
                                     title='Summed sizes of outgoing synapses globally normalised',
                                     filename=f_name, cmap=cmap_heatmap)
    out_sizes_abs_sum_dn.get_heatmap(save_svg=save_svg, annot=annot, fontsize=fontsize)

    log.info('Connectivity analysis finished')