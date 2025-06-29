#analysis to see if MSN from same LMAN inhibit each other and then see if they project to same GPs
#similar analysis that MSN2MSN_GP_inhibition but starting point at LMAN input
#based on domain hypothesis published by Wicken et al., 1993, 1995

if __name__ == '__main__':
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_conn_helper import filter_synapse_caches_for_ct
    from cajal.nvmescratch.users.arother.bio_analysis.general.result_helper import ResultsForPlotting, ComparingResultsForPLotting
    import time
    from syconn.handler.config import initialize_logging
    from syconn import global_params
    from syconn.reps.segmentation import SegmentationDataset
    import os as os
    import pandas as pd
    from syconn.handler.basics import write_obj2pkl, load_pkl2obj
    import numpy as np
    from tqdm import tqdm
    from scipy.stats import ranksums
    import matplotlib.pyplot as plt
    import seaborn as sns
    from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_params import Analysis_Params

    version = 'v6'
    bio_params = Analysis_Params(version=version)
    global_params.wd = bio_params.working_dir()
    sd_synssv = SegmentationDataset("syn_ssv", working_dir=global_params.config.working_dir)
    ct_dict = bio_params.ct_dict()
    min_comp_len = 200
    max_MSN_path_len = 7500
    syn_prob = 0.6
    min_syn_size = 0.1
    msn_ct = 3
    lman_ct = 1
    gpi_ct = 7
    f_name = f"cajal/scratch/users/arother/bio_analysis_results/LMAN_MSN_analysis/" \
             f"240227_j0251{version}_lman_msn2msn_mcl{min_comp_len}_syn{syn_prob}"
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    log = initialize_logging('LMAN MSN to MSN inhibition analysis', log_dir=f_name + '/logs/')
    log.info(f"min_comp_len ={min_comp_len} µm, use handpicked LMAN axons, "
             f"syn_prob = {syn_prob}, min_syn_size = {min_syn_size} µm")

    #load LMAN and MSN dictionaries from LMAN_MSN_number est. to get MSN ids LMAN
    #prjects to and GPi ids MSN project to

    LMAN_proj_dict = load_pkl2obj(
        f"cajal/scratch/users/arother/bio_analysis_results/LMAN_MSN_analysis/" \
                       f"240227_j0251{version}_lman_number_msn_mcl{min_comp_len}_syn{syn_prob}/lman_dict_percell.pkl" )
    MSN_proj_dict = load_pkl2obj(
        f"cajal/scratch/users/arother/bio_analysis_results/LMAN_MSN_analysis/" \
                       f"240227_j0251{version}_lman_number_msn_mcl{min_comp_len}_syn{syn_prob}//msn_proj_dict_percell.pkl")
    msn_ids = list(MSN_proj_dict.keys())
    lman_ids = list(LMAN_proj_dict.keys())

    #1st step: get synapses between MSN cells from MSN proj dict
    log.info("Step 1/3: get MSN-MSN inhibition information from synapses")
    #prefilter for only MSN to MSN axo-dendritic synapses
    m_cts, m_ids, m_axs, m_ssv_partners, m_sizes, m_spiness, m_rep_coord = filter_synapse_caches_for_ct(sd_synssv = sd_synssv,
                                                                                                        pre_cts=[
                                                                                                            msn_ct],
                                                                                                        post_cts=[
                                                                                                            msn_ct],
                                                                                                        syn_prob_thresh=syn_prob,
                                                                                                        min_syn_size=min_syn_size,
                                                                                                        axo_den_so=True)

    #filter synapses to only include ones from msn_inds to msn_inds
    msnids_inds = np.all(np.in1d(m_ssv_partners, msn_ids).reshape(len(m_ssv_partners), 2), axis=1)
    m_cts = m_cts[msnids_inds]
    m_ids = m_ids[msnids_inds]
    m_ssv_partners = m_ssv_partners[msnids_inds]
    m_sizes = m_sizes[msnids_inds]
    m_axs = m_axs[msnids_inds]

    #get overall number of synapses each msn synapses to
    ax_inds = np.where(m_axs == 1)
    ax_ssvsids = m_ssv_partners[ax_inds]
    ax_ssv_inds, unique_axmsn_ssvs = pd.factorize(ax_ssvsids)
    msn_syn_sumsizes = np.bincount(ax_ssv_inds, m_sizes)
    msn_syn_number = np.bincount(ax_ssv_inds)

    #get per all MSN cells one MSN synapses to
    denso_inds = np.where(m_axs != 1)
    denso_ssvids = m_ssv_partners[denso_inds]
    msn_ssv_pd = pd.DataFrame(denso_ssvids)
    permsn_ids_grouped = msn_ssv_pd.groupby(by=ax_ssv_inds)
    permsn_msn_groups = permsn_ids_grouped.groups

    MSN_inh_dict_percell = {id: {"MSN ids": np.unique(denso_ssvids[permsn_msn_groups[i]]),
                                 "number MSN cells": len(np.unique(denso_ssvids[permsn_msn_groups[i]]))} for
                            i, id in enumerate(unique_axmsn_ssvs)}
    number_msn_permsn = np.array([MSN_inh_dict_percell[msn]["number MSN cells"] for msn in MSN_inh_dict_percell])
    MSN_overall_inh_dict = {"MSN ids": unique_axmsn_ssvs, "number of synapses from MSN": msn_syn_number,
                    "sum size synapses from MSN": msn_syn_sumsizes,
                    "number MSN cells": number_msn_permsn,
                    "number of synapses per MSN": msn_syn_number / number_msn_permsn,
                    "sum size synapses per MSM": msn_syn_sumsizes / number_msn_permsn}

    write_obj2pkl("%s/msn_inh_percell.pkl" % f_name, MSN_inh_dict_percell)
    write_obj2pkl("%s/msn_inh_dict.pkl" % f_name, MSN_overall_inh_dict)
    msn_overall_pd = pd.DataFrame(MSN_overall_inh_dict)
    msn_overall_pd.to_csv("%s/msn_inh_dict.csv" % f_name)
    msn_plotting = ResultsForPlotting(celltype = ct_dict[msn_ct], dictionary = MSN_overall_inh_dict, filename = f_name)
    for key in MSN_overall_inh_dict:
        if "ids" in key:
            continue
        if "cells" in key:
            msn_plotting.plot_hist(key, subcell="cells", cells=True)
        else:
            msn_plotting.plot_hist(key, subcell="synapse", cells=False)

    log.info("Number of MSMs inhibiting other MSNs which get input from LMAN and output to GPi: %i" % len(unique_axmsn_ssvs))
    log.info("Average number of MSNs inhibited per MSN overall = %.2f" % np.mean(number_msn_permsn))
    log.info("Median number of MSNs inhibited per MSN overall = %.2f" % np.median(number_msn_permsn))

    #2nd step: iterate over all LMANs to see if there is inhibition among MSNs and if it is targeting the same GPs
    log.info("Step 2/3: Iterate over LMAN to see inhibition within MSNs targeted by same LMAN")
    number_msn_inhibitions_per_lman = np.zeros(len(lman_ids))
    number_msns_inhibiting_per_lman = np.zeros(len(lman_ids))
    number_msn_inhibiton_pairs_bothdirections_per_lman = np.zeros(len(lman_ids))
    perlman_inhibitionspairs_sameGPi_number = np.zeros(len(lman_ids))
    perlman_inhibitionspairs_differentGPi_number = np.zeros(len(lman_ids))
    per_lman_number_inhpairs_only_same_GPi = np.zeros(len(lman_ids))
    per_lman_number_inhpairs_only_different_GPi = np.zeros(len(lman_ids))
    per_lman_number_inhpairs_same_diff_GPi = np.zeros(len(lman_ids))
    msn_pair_both_directions_dict = dict()
    msn_pair_oneway_dict = dict()
    for li, lman_id in enumerate(tqdm(lman_ids)):
        msns_per_lman = LMAN_proj_dict[lman_id]["MSN ids"]
        inhibiting_msns = 0
        inhibited_msns = 0
        same_GPis = 0
        different_GPis = 0
        inh_pair_same_GPi = 0
        inh_pair_diff_GPi = 0
        inh_pair_same_diff_GPi = 0
        msn_pairs = []
        msn_pairs_bothdirections = 0
        for msn_id in msns_per_lman:
            if msn_id not in MSN_inh_dict_percell.keys():
                continue
            inhibiting_msns += 1
            inh_msns = MSN_inh_dict_percell[msn_id]["MSN ids"]
            inhibited_msns += len(inh_msns)
            gpis_ax_msn = MSN_proj_dict[msn_id]["GPi ids"]
            for inh_msn in inh_msns:
                inh_gpis = MSN_proj_dict[inh_msn]["GPi ids"]
                gpi_comparison = np.in1d(gpis_ax_msn, inh_gpis)
                number_same_GPis = len(gpis_ax_msn[gpi_comparison])
                number_diff_GPis = len(gpis_ax_msn[gpi_comparison == False])
                same_GPis += number_same_GPis
                different_GPis += number_diff_GPis
                if number_same_GPis > 0:
                    if number_diff_GPis > 0:
                        inh_pair_same_diff_GPi += 1
                    else:
                        inh_pair_same_GPi += 1
                else:
                    inh_pair_diff_GPi += 1
                msn_pairs.append([msn_id, inh_msn])
                if [lman_id, inh_msn, msn_id] in msn_pairs:
                    msn_pair_oneway_dict.pop([msn_id, inh_msn])
                    msn_pair_both_directions_dict[(lman_id, msn_id, inh_msn)] = {"number same GPi": number_same_GPis,
                                                                         "number different GPi": number_diff_GPis}
                else:
                    msn_pair_oneway_dict[(lman_id, msn_id, inh_msn)] = {"number same GPi": number_same_GPis, "number different GPi": number_diff_GPis}
        #get results per LMAN
        number_msn_inhibitions_per_lman[li] = inhibited_msns
        number_msns_inhibiting_per_lman[li] = inhibiting_msns
        number_msn_inhibiton_pairs_bothdirections_per_lman[li] = msn_pairs_bothdirections
        perlman_inhibitionspairs_differentGPi_number[li] = different_GPis
        perlman_inhibitionspairs_sameGPi_number[li] = same_GPis
        per_lman_number_inhpairs_only_different_GPi[li] = inh_pair_diff_GPi
        per_lman_number_inhpairs_only_same_GPi[li] = inh_pair_same_GPi
        per_lman_number_inhpairs_same_diff_GPi[li] = inh_pair_same_diff_GPi

    percentage_onlysameGPi_perlman = per_lman_number_inhpairs_only_same_GPi / number_msns_inhibiting_per_lman
    percentage_onlydiffGPi_perlman = per_lman_number_inhpairs_only_different_GPi / number_msns_inhibiting_per_lman
    percentage_samediffGPi_perlman = per_lman_number_inhpairs_same_diff_GPi / number_msns_inhibiting_per_lman

    per_LMAN_result_dict = {"LMAN ids": lman_ids,"Number of inhibited MSNs per LMAN": number_msn_inhibitions_per_lman,
                            "Number of inhibiting MSNs per LMAN": number_msns_inhibiting_per_lman,
                            "Number of MSN pairs inhibiting each other per LMAN": number_msn_inhibiton_pairs_bothdirections_per_lman,
                            "Number of different GPi from MSN inhibition pairs per LMAN": perlman_inhibitionspairs_differentGPi_number,
                            "Number of same GPi from MSN inhibition pairs per LMAN": perlman_inhibitionspairs_sameGPi_number,
                            "Number of MSN inhibition pairs only projecting to same GPi per LMAN": per_lman_number_inhpairs_only_same_GPi,
                            "Number of MSN inhibition pairs only projecting to different GPi per LMAN": per_lman_number_inhpairs_only_different_GPi,
                            "Number of MSN inhibition pairs projecting to same and different GPi per LMAN": per_lman_number_inhpairs_same_diff_GPi}

    write_obj2pkl("%s/per_lman_results.pkl" % f_name, per_LMAN_result_dict)
    per_LMAN_results_pd = pd.DataFrame(per_LMAN_result_dict)
    per_LMAN_results_pd.to_csv("%s/per_lman_results.csv" % f_name)


    #also get results pairwise to compare pairs of MSN that inhibit each other and that only inhibit one direction
    msn_pairs_both_dir = list(msn_pair_both_directions_dict.keys())
    lman_bd = np.zeros(len(msn_pairs_both_dir))
    number_pairs_both_dir = len(msn_pairs_both_dir)
    both_dir_msn1 = np.zeros(number_pairs_both_dir)
    both_dir_msn2 = np.zeros(number_pairs_both_dir)
    both_dir_number_same_GPi = np.zeros(number_pairs_both_dir)
    both_dir_number_diff_GPi = np.zeros(number_pairs_both_dir)

    for i, pair in enumerate(tqdm(msn_pairs_both_dir)):
        lman_bd[i] = pair[0]
        both_dir_msn1[i] = pair[1]
        both_dir_msn2[i] = pair[2]
        both_dir_number_diff_GPi[i] = msn_pair_both_directions_dict[pair]["number different GPi"]
        both_dir_number_same_GPi[i] = msn_pair_both_directions_dict[pair]["number same GPi"]

    both_dir_pairwise_results = {"LMAN id": lman_bd, "MSN 1 id": both_dir_msn1, "MSN 2 id": both_dir_msn2,
                                 "number same GPi": both_dir_number_same_GPi, "number different GPi": both_dir_number_diff_GPi}
    write_obj2pkl("%s/pairwise_both_directions_samelman.pkl" % f_name, both_dir_pairwise_results)
    both_dir_pd = pd.DataFrame(both_dir_pairwise_results)
    both_dir_pd.to_csv("%s/pairwise_both_directions_samelman.csv" % f_name)

    msn_pairs_oneway = list(msn_pair_oneway_dict.keys())
    number_pairs_oneway = len(msn_pairs_oneway)
    lman_ow = np.zeros(len(msn_pairs_oneway))
    ow_dir_msn1 = np.zeros(number_pairs_oneway)
    ow_dir_msn2 = np.zeros(number_pairs_oneway)
    ow_dir_number_same_GPi = np.zeros(number_pairs_oneway)
    ow_dir_number_diff_GPi = np.zeros(number_pairs_oneway)

    for i, pair in enumerate(tqdm(msn_pairs_oneway)):
        lman_ow[i] = pair[0]
        ow_dir_msn1[i] = pair[1]
        ow_dir_msn2[i] = pair[2]
        ow_dir_number_diff_GPi[i] = msn_pair_oneway_dict[pair]["number different GPi"]
        ow_dir_number_same_GPi[i] = msn_pair_oneway_dict[pair]["number same GPi"]

    ow_pairwise_results = {"LMAN id": lman_ow, "MSN 1 id": ow_dir_msn1, "MSN 2 id": ow_dir_msn2,
                                 "number same GPi": ow_dir_number_same_GPi,
                                 "number different GPi": ow_dir_number_diff_GPi}
    write_obj2pkl("%s/pairwise_one_way_samelman.pkl" % f_name, ow_pairwise_results)
    ow_pd = pd.DataFrame(ow_pairwise_results)
    ow_pd.to_csv("%s/pairwise_one_way_samelman.csv" % f_name)

    log.info("Average number of MSN pairs per LMAN that inhibit each other = %.2f" % np.mean(number_pairs_both_dir))
    log.info("Average number of MSNs per LMAN projecting only to same GPis as MSNs they inhibited = %.2f" % np.mean(per_lman_number_inhpairs_only_same_GPi))
    log.info("Average number of MSNs per LMAN projecting only to different GPis as MSNs they inhibited = %.2f" % np.mean(
        per_lman_number_inhpairs_only_different_GPi))
    log.info("Average percentage of MSNs per LMAN projecting only to same GPis as MSNs they inhibited = %.2f" % np.mean(
        percentage_onlysameGPi_perlman))
    log.info(
        "Average percentage of MSNs per LMAN projecting only to different GPis as MSNs they inhibited = %.2f" % np.mean(
            percentage_onlydiffGPi_perlman))
    log.info(
        "Median number of MSN pairs per LMAN that inhibit each other = %.2f" % np.median(number_pairs_both_dir))
    log.info("Median number of MSNs per LMAN projecting only to same GPis as MSNs they inhibited = %.2f" % np.median(
        per_lman_number_inhpairs_only_same_GPi))
    log.info(
        "Median number of MSNs per LMAN projecting only to different GPis as MSNs they inhibited = %.2f" % np.median(
            per_lman_number_inhpairs_only_different_GPi))
    log.info(
        "Median percentage of MSNs per LMAN projecting only to same GPis as MSNs they inhibited = %.2f" % np.median(
            percentage_onlysameGPi_perlman))
    log.info(
        "Median percentage of MSNs per LMAN projecting only to different GPis as MSNs they inhibited = %.2f" % np.median(
            percentage_onlydiffGPi_perlman))


    time_stamps = [time.time()]
    step_idents = ['get MSN to MSN inhibiton per LMAN']

    log.info("Step 3/3: Plot results, pairwise and per LMAN axon")
    #plot results per LMAN as histograms
    lman_plotting = ResultsForPlotting(celltype=ct_dict[lman_ct], dictionary=per_LMAN_result_dict, filename=f_name)
    for key in per_LMAN_result_dict.keys():
        if "ids" in key:
            continue
        if "MSN pairs" in key or "MSN inhibition pairs" in key:
            lman_plotting.plot_hist(key, subcell="pairs", cells=False)
        else:
            lman_plotting.plot_hist(key, subcell="cells", cells=True)

    #compare results of pairs in both directions and pairs only in one direction
    #only if actually pairs that inhibit each other
    keys = list(ow_pairwise_results.keys())
    if number_pairs_both_dir > 0:
        pair_results_for_plotting = ComparingResultsForPLotting(celltype1="pairs inhibiting each other", celltype2="pairs one direction",
                                                          dictionary1=both_dir_pairwise_results,
                                                          dictionary2=ow_pairwise_results, color1='#60A6A6', color2='#051A26',
                                                          filename=f_name)
        ranksum_results = pd.DataFrame(columns=keys[1:], index=["stats", "p value"])
        for key in keys:
            if "id" in key:
                continue
            stats, p_value = ranksums(both_dir_pairwise_results[key], ow_pairwise_results[key])
            ranksum_results.loc["stats", key] = stats
            ranksum_results.loc["p value", key] = p_value
            sns.distplot(both_dir_pd[key],
                         hist_kws={"histtype": "step", "linewidth": 3, "alpha": 1},
                         kde=False, norm_hist=False, bins=10, label="pairs inhibiting each other", color='#60A6A6')
            sns.distplot(ow_pd[key],
                         hist_kws={"histtype": "step", "linewidth": 3, "alpha": 1},
                         kde=False, norm_hist=False, bins=10, label="pairs one direction", color='#051A26')
            plt.legend()
            plt.xlabel(key)
            plt.ylabel("count of cell pairs")
            plt.savefig("%s/%s_hist_comparison.svg" % (f_name, key))
            plt.savefig("%s/%s_hist_comparison.png" % (f_name, key))
            plt.close()
            sns.distplot(both_dir_pd[key],
                         hist_kws={"histtype": "step", "linewidth": 3, "alpha": 1},
                         kde=False, norm_hist=True, bins=10, label="pairs inhibiting each other", color='#60A6A6')
            sns.distplot(ow_pd[key],
                         hist_kws={"histtype": "step", "linewidth": 3, "alpha": 1},
                         kde=False, norm_hist=True, bins=10, label="pairs one direction", color='#051A26')
            plt.legend()
            plt.xlabel(key)
            plt.ylabel("count of cell pairs")
            plt.savefig("%s/%s_hist_comparison_norm.svg" % (f_name, key))
            plt.savefig("%s/%s_hist_comparison_norm.png" % (f_name, key))
            plt.close()
            result_df = pair_results_for_plotting.result_df_per_param(key)
            pair_results_for_plotting.plot_violin(result_df=result_df, key=key, subcell="cell pairs")

        ranksum_results.to_csv("%s/ranksum_results.csv" % f_name)
    else:
        ow_results_for_plotting = ResultsForPlotting(celltype = ct_dict[lman_ct], dictionary = ow_pairwise_results, filename = f_name)
        for key in keys:
            if "id" in key:
                continue
            ow_results_for_plotting.plot_hist(key, subcell="cell pairs", cells=False)

    log.info("MSN to MSN inhibition analysis per LMAN axon finished")





