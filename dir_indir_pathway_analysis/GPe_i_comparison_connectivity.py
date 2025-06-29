#script for looking at GPe/i connectivity with FS, STN, TAN

if __name__ == '__main__':
    from cajal.nvmescratch.users.arother.bio_analysis.dir_indir_pathway_analysis.connectivity_between2cts import synapses_between2cts, compare_connectivity
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_params import Analysis_Params
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_morph_helper import check_comp_lengths_ct
    from cajal.nvmescratch.users.arother.bio_analysis.dir_indir_pathway_analysis.compartment_volume_celltype import \
        axon_den_arborization_ct, compare_compartment_volume_ct
    import time
    from syconn.handler.config import initialize_logging
    from syconn import global_params
    from syconn.reps.super_segmentation import SuperSegmentationDataset, SuperSegmentationObject
    from syconn.reps.segmentation import SegmentationDataset
    import os as os
    import pandas as pd
    from cajal.nvmescratch.users.arother.bio_analysis.general.result_helper import plot_nx_graph
    from syconn.handler.basics import write_obj2pkl, load_pkl2obj
    import numpy as np

    global_params.wd = "/cajal/nvmescratch/projects/data/songbird_tmp/j0251/j0251_72_seg_20210127_agglo2_syn_20220811"

    ssd = SuperSegmentationDataset(working_dir=global_params.config.working_dir)
    sd_synssv = SegmentationDataset("syn_ssv", working_dir=global_params.config.working_dir)
    start = time.time()
    comp_length_cell = 200
    #comp_length_cell_ax = 50
    syn_prob = 0.6
    gpe_ct = 6
    gpi_ct = 7
    f_name = "cajal/scratch/users/arother/bio_analysis_results/dir_indir_pathway_analysis/231025_j0251v5_GPe_i_comparison_mcl_%i_synprob_%.2f" % (comp_length_cell, syn_prob)
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    log = initialize_logging('GPe, GPi comparison connectivity', log_dir=f_name + '/logs/')
    log.info("GPe/i comparison starts")
    time_stamps = [time.time()]
    step_idents = ['t-0']
    #ct_dict = {0: "STN", 1: "DA", 2: "MSN", 3: "LMAN", 4: "HVC", 5: "TAN", 6: "GPe", 7: "GPi", 8: "FS", 9: "LTS",
                   #10: "NGF"}
    analysis_params = Analysis_Params(working_dir = global_params.wd, version = 'v5')

    known_mergers = analysis_params.load_known_mergers()
    GPi_full_cell_dict = analysis_params.load_cell_dict(gpi_ct)
    GPi_ids = np.array(list(GPi_full_cell_dict.keys()))
    merger_inds = np.in1d(GPi_ids, known_mergers) == False
    GPi_ids = GPi_ids[merger_inds]
    GPi_ids = check_comp_lengths_ct(cellids=GPi_ids, fullcelldict=GPi_full_cell_dict, min_comp_len=comp_length_cell,
                                    axon_only=False,
                                    max_path_len=None)

    GPe_full_cell_dict = analysis_params.load_cell_dict(gpe_ct)
    GPe_ids = np.array(list(GPe_full_cell_dict.keys()))
    merger_inds = np.in1d(GPe_ids, known_mergers) == False
    GPe_ids = GPe_ids[merger_inds]
    GPe_ids = check_comp_lengths_ct(cellids=GPe_ids, fullcelldict=GPe_full_cell_dict, min_comp_len=comp_length_cell,
                                    axon_only=False,
                                    max_path_len=None)

    log.info("Step 1/5: GPe/i compartment comparison")
    # calculate parameters such as axon/dendrite length, volume, tortuosity and compare within celltypes
    result_GPe_filename = axon_den_arborization_ct(ssd, celltype=6, filename=f_name, cellids = GPe_ids, full_cell_dict = GPe_full_cell_dict, min_comp_len = comp_length_cell)
    result_GPi_filename = axon_den_arborization_ct(ssd, celltype=7, filename=f_name, cellids = GPi_ids, full_cell_dict = GPi_full_cell_dict, min_comp_len = comp_length_cell)
    compare_compartment_volume_ct(celltype1=6, celltype2=7, filename=f_name, filename1=result_GPe_filename, filename2=result_GPi_filename,
                                  percentile=None, min_comp_len = comp_length_cell, color_key = 'STNGP')

    time_stamps = [time.time()]
    step_idents = ["compartment comparison finished"]


    log.info("Step 2/5: GPe and GPi connectivity")
    # see how GPe and GPi are connected
    GPe_GPi_connectivity_resultsfolder = synapses_between2cts(sd_synssv, celltype1=6, celltype2=7, filename=f_name,
                                                              cellids1 = GPe_ids, cellids2 = GPi_ids, full_cells=True,
                                                              min_comp_len = comp_length_cell, syn_prob_thresh = syn_prob,
                                                              wd = global_params.wd, version = 'v5')
    GPe_i_sum_synapses = compare_connectivity(comp_ct1=6, comp_ct2=7, filename=f_name, foldername_ct1=GPe_GPi_connectivity_resultsfolder,
                                              foldername_ct2=GPe_GPi_connectivity_resultsfolder, min_comp_len = comp_length_cell)

    time_stamps = [time.time()]
    step_idents = ["connctivity among GPe/i finished"]

    MSN_dict = analysis_params.load_cell_dict(celltype=2)
    MSN_ids = np.array(list(MSN_dict.keys()))
    merger_inds = np.in1d(MSN_ids, known_mergers) == False
    MSN_ids = MSN_ids[merger_inds]
    misclassified_asto_ids = analysis_params.load_potential_astros()
    astro_inds = np.in1d(MSN_ids, misclassified_asto_ids) == False
    MSN_ids = MSN_ids[astro_inds]
    MSN_ids = check_comp_lengths_ct(cellids=MSN_ids, fullcelldict=MSN_dict, min_comp_len=comp_length_cell,
                                    axon_only=False,
                                    max_path_len=None)

    log.info("Step 3/5: GPe/i - MSN connectivity")
    # see how GPe and GPi are connected to STN
    GPe_MSN_connectivity_resultsfolder = synapses_between2cts(sd_synssv, celltype1=6, celltype2=2, filename=f_name,
                                                              full_cells=True, cellids1 = GPe_ids, cellids2 = MSN_ids,
                                                              min_comp_len=comp_length_cell, syn_prob_thresh = syn_prob,
                                                              wd = global_params.wd, version = 'v5')
    GPi_MSN_connectivity_resultsfolder = synapses_between2cts(sd_synssv, celltype1=7, celltype2=2, filename=f_name,
                                                              full_cells=True, cellids1 = GPi_ids, cellids2 = MSN_ids,
                                                              min_comp_len=comp_length_cell, syn_prob_thresh = syn_prob,
                                                              wd = global_params.wd, version = 'v5')
    GPe_i_MSN_sum_synapses = compare_connectivity(comp_ct1=6, comp_ct2=7, connected_ct=2, filename=f_name,
                                                  foldername_ct1=GPe_MSN_connectivity_resultsfolder,
                                                  foldername_ct2=GPi_MSN_connectivity_resultsfolder,
                                                  min_comp_len=comp_length_cell)

    time_stamps = [time.time()]
    step_idents = ["connctivity GPe/i - MSN finished"]

    STN_ids = analysis_params.load_full_cell_array(celltype=0)
    

    log.info("Step 3/5: GPe/i - STN connectivity")
    # see how GPe and GPi are connected to STN
    GPe_STN_connectivity_resultsfolder = synapses_between2cts(sd_synssv, celltype1=6, celltype2=0, filename=f_name, full_cells=True, cellids1 = GPe_ids,
                                                              cellids2 = STN_ids, min_comp_len = comp_length_cell,
                                                              syn_prob_thresh = syn_prob, wd = global_params.wd, version = 'v5')
    GPi_STN_connectivity_resultsfolder = synapses_between2cts(sd_synssv, celltype1=7, celltype2=0, filename=f_name, full_cells=True,
                                                              cellids1 = GPi_ids, cellids2 = STN_ids,
                                                              min_comp_len = comp_length_cell, syn_prob_thresh = syn_prob,
                                                              wd = global_params.wd, version = 'v5')
    GPe_i_STN_sum_synapses = compare_connectivity(comp_ct1=6, comp_ct2=7, connected_ct=0, filename=f_name, foldername_ct1=GPe_STN_connectivity_resultsfolder,
                                                  foldername_ct2=GPi_STN_connectivity_resultsfolder, min_comp_len = comp_length_cell)

    time_stamps = [time.time()]
    step_idents = ["connctivity GPe/i - STN finished"]

    FS_ids = analysis_params.load_full_cell_array(celltype=8)

    log.info("Step 4/5: GPe/i - FS connectivity")
    # see how GPe and GPi are connected to FS
    GPe_FS_connectivity_resultsfolder = synapses_between2cts(sd_synssv, celltype1=6, celltype2=8, filename=f_name, full_cells=True,
                                                             cellids1 = GPe_ids, cellids2 = FS_ids,
                                                             syn_prob_thresh = syn_prob, min_comp_len = comp_length_cell,
                                                             wd = global_params.wd, version = 'v5')
    GPi_FS_connectivity_resultsfolder = synapses_between2cts(sd_synssv, celltype1=7, celltype2=8, filename=f_name,
                                                             full_cells=True, cellids1 = GPi_ids, cellids2 = FS_ids,
                                                             syn_prob_thresh = syn_prob, min_comp_len = comp_length_cell,
                                                             wd = global_params.wd, version = 'v5')
    GPe_i_FS_sum_synapses = compare_connectivity(comp_ct1=6, comp_ct2=7, connected_ct=8, filename=f_name, foldername_ct1=GPe_FS_connectivity_resultsfolder,
                                                 foldername_ct2=GPi_FS_connectivity_resultsfolder, min_comp_len = comp_length_cell)

    time_stamps = [time.time()]
    step_idents = ["connctivity GPe/i - FS finished"]

    TAN_ids = analysis_params.load_full_cell_array(celltype=5)

    log.info("Step 5/5: GPe/i - TAN connectivity")
    # see how GPe and GPi are connected to TAN
    GPe_TAN_connectivity_resultsfolder = synapses_between2cts(sd_synssv, celltype1=6, celltype2=5, filename=f_name,
                                                              full_cells=True, cellids1 = GPe_ids, cellids2 = TAN_ids,
                                                              syn_prob_thresh = syn_prob, min_comp_len = comp_length_cell,
                                                              wd = global_params.wd, version = 'v5')
    GPi_TAN_connectivity_resultsfolder = synapses_between2cts(sd_synssv, celltype1=7, celltype2=5, filename=f_name,
                                                              full_cells=True, cellids1 = GPi_ids, cellids2 = TAN_ids,
                                                              syn_prob_thresh = syn_prob, min_comp_len = comp_length_cell,
                                                              wd = global_params.wd, version = 'v5')
    GPe_i_TAN_sum_synapses = compare_connectivity(comp_ct1=6, comp_ct2=7, connected_ct=5, filename=f_name, foldername_ct1=GPe_TAN_connectivity_resultsfolder,
                                                  foldername_ct2=GPi_TAN_connectivity_resultsfolder, min_comp_len = comp_length_cell)

    time_stamps = [time.time()]
    step_idents = ["connctivity GPe/i - TAN finished"]


    log.info("Step 9/9 Overview Graph")
    # make connectivity overview graph with networkx
    #first put all dictionaries together
    sum_synapse_dict = {**GPe_i_sum_synapses, **GPe_i_STN_sum_synapses, **GPe_i_FS_sum_synapses, **GPe_i_TAN_sum_synapses}
    write_obj2pkl("%s/ct_sum_synapses.pkl" % f_name, sum_synapse_dict)
    #plot
    plot_nx_graph(sum_synapse_dict, filename = ("%s/summed_synapses_nx_overview_mcl%i.png" % (f_name, comp_length_cell)), title = "sum of synapses between celltypes")

    msn_summed_synapse_pd = pd.DataFrame(sum_synapse_dict, index=[0])
    msn_summed_synapse_pd.to_csv("%s/ct_summed_synapses.csv" % f_name)

    log.info("GPe/i compartment and connectivity analysis finished")
    step_idents = ["GPe/i compartment and connectivity analysis finished"]


