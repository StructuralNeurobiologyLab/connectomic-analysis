
from syconn import global_params
from syconn.reps.super_segmentation import SuperSegmentationDataset
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import os as os
import scipy
import time
from syconn.handler.config import initialize_logging
from syconn.handler.basics import load_pkl2obj
from syconn.handler.basics import write_obj2pkl
from scipy.stats import ranksums, kruskal
from cajal.nvmescratch.users.arother.bio_analysis.general.result_helper import ResultsForPlotting, ComparingResultsForPLotting, ComparingMultipleForPLotting
from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_morph_helper import get_compartment_length, get_compartment_bbvolume, \
    get_compartment_radii, get_compartment_tortuosity_complete, get_compartment_tortuosity_sampled, get_spine_density, get_cell_soma_radius
from syconn.reps.super_segmentation import SuperSegmentationObject
from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_colors import CelltypeColors
from syconn.mp.mp_utils import start_multiprocess_imap
from itertools import combinations

global_params.wd = "/cajal/nvmescratch/projects/data/songbird_tmp/j0251/j0251_72_seg_20210127_agglo2_syn_20220811"

ssd = SuperSegmentationDataset(working_dir=global_params.config.working_dir)

def comp_aroborization(sso, compartment, cell_graph, min_comp_len = 100, full_cell_dict = None):
    """
    calculates bounding box from min and max dendrite values in each direction to get a volume estimation per compartment.
    :param sso: cell
    :param compartment: 0 = dendrite, 1 = axon, 2 = soma
    :param cell_graph: sso.weighted graph
    :param min_comp_len: minimum compartment length, if not return 0
    :param full_cell_dict: dictionary holding per cell parameters for lookup, expects to be already for cellid
    :return: comp_len, comp_volume in µm³
    """
    # use full cell dict to lookup versions
    comp_dict = {1: "axon", 0: "dendrite"}
    if full_cell_dict is not None:
        try:
            comp_length = full_cell_dict[comp_dict[compartment] + " length"]
        except KeyError:
            comp_length = get_compartment_length(sso, compartment, cell_graph)
    else:
        comp_length = get_compartment_length(sso, compartment, cell_graph)
    if comp_length < min_comp_len:
        return 0, 0, 0, 0, 0
    comp_inds = np.nonzero(sso.skeleton["axoness_avg10000"] == compartment)[0]
    comp_nodes = sso.skeleton["nodes"][comp_inds] * sso.scaling
    comp_volume = get_compartment_bbvolume(comp_nodes)
    comp_radii = get_compartment_radii(cell = sso, comp_inds = comp_inds)
    median_comp_radius = np.median(comp_radii)
    tortuosity_complete = get_compartment_tortuosity_complete(comp_length, comp_nodes)
    tortosity_sampled = get_compartment_tortuosity_sampled(cell_graph, comp_nodes)
    return comp_length, comp_volume, median_comp_radius, tortuosity_complete, tortosity_sampled

def axon_dendritic_arborization_cell(input):
    '''
    analysis the spatial distribution of the axonal/dendritic arborization per cell if they fulfill the minimum compartment length.
    To estimate the volume a dendritic arborization spans, the bounding box around the axon or dendrite is estimated by its min and max values in each direction.
    Uses comp_arborization.
    :param min_comp_len: minimum compartment length of axon and dendrite
    :param full_cell_dict: dictionary with cached values. already calles for one cell
    :param spiness: if True: calculate spine density per cell
    :return: overall axonal/dendritic length [µm], axonal/dendritic volume [µm³]
    '''
    cellid, min_comp_len, full_cell_dict, spiness = input
    sso = SuperSegmentationObject(cellid)
    sso.load_skeleton()
    g = sso.weighted_graph(add_node_attr=('axoness_avg10000',))
    if full_cell_dict is not None:
        axon_length, axon_volume, ax_median_radius, ax_tortuosity_complete, ax_tortuosity_sampled = comp_aroborization(
            sso, compartment=1, cell_graph=g, min_comp_len=min_comp_len, full_cell_dict = full_cell_dict)
    else:
        axon_length, axon_volume, ax_median_radius, ax_tortuosity_complete, ax_tortuosity_sampled = comp_aroborization(sso, compartment=1, cell_graph=g, min_comp_len = min_comp_len)
    if axon_length == 0:
        return 0, 0
    if full_cell_dict is not None:
        dendrite_length, dendrite_volume, dendrite_median_radius, dendrite_tortuosity_complete, dendrite_tortuosity_sampled = comp_aroborization(sso, compartment=0, cell_graph=g,
                                                                              min_comp_len=min_comp_len,full_cell_dict= full_cell_dict)
    else:
        dendrite_length, dendrite_volume, dendrite_median_radius, dendrite_tortuosity_complete, dendrite_tortuosity_sampled = comp_aroborization(
            sso, compartment=0, cell_graph=g,
            min_comp_len=min_comp_len)
    if dendrite_length == 0:
        return 0, 0
    ax_dict = {"length": axon_length, "volume": axon_volume, "median radius": ax_median_radius, "tortuosity complete": ax_tortuosity_complete, "tortuosity sampled": ax_tortuosity_sampled}
    den_dict = {"length": dendrite_length, "volume": dendrite_volume, "median radius": dendrite_median_radius, "tortuosity complete": dendrite_tortuosity_complete, "tortuosity sampled": dendrite_tortuosity_sampled}
    if spiness:
        input = [cellid, min_comp_len, full_cell_dict]
        den_dict["spine density"] = get_spine_density(input)[0]
    return np.array([ax_dict, den_dict])

def axon_den_arborization_ct(ssd, celltype, filename, cellids, ct_dict, min_comp_len = 100, full_cell_dict = None, percentile = None, label_cts = None, spiness = False):
    '''
    estimate the axonal and dendritic aroborization by celltype. Uses axon_dendritic_arborization to get the aoxnal/dendritic bounding box volume per cell
    via comp_arborization. Plots the volume per compartment and the overall length as histograms.
    :param ssd: super segmentation dataset
    :param celltype: j0256: STN=0, DA=1, MSN=2, LMAN=3, HVC=4, TAN=5, GPe=6, GPi=7,
#                      FS=8, LTS=9, NGF=10
    :param filename: filename to save plots in
    :param cellids: cellids for analysis
    :param ct_dict: dictionary showing which celltype number belongs to which celltype
    :param min_comp_len: minimum compartment length in µm
    :param full_cells_dict: cached dictionary related to celltype
    :param handpicked: loads cells that were manually checked
    :param if percentile given, percentile of the cell population can be compared, if preprocessed, in case of 50 have to give either 49 or 51
    :param label_cts: celltype label, if subgroup and deviating from ct_dict, if None: take ct_dict celltype label
    :param spiness: if True, also calculate spine density
    :return: f_name: foldername in which results are stored
    '''

    if percentile is not None:
        if percentile == 50:
            raise ValueError("Due to ambiguity, value has to be either 49 or 51")
        else:
            ct_dict[celltype] = ct_dict[celltype] + " p%.2i" % percentile
    if label_cts is None:
        if percentile is not None:
            if percentile == 50:
                raise ValueError("Due to ambiguity, value has to be either 49 or 51")
            else:
                label_cts = ct_dict[celltype] + " p%.2i" % percentile
        else:
            label_cts = ct_dict[celltype]
    f_name = "%s/%s_comp_volume_mcl%i" % (filename, label_cts, min_comp_len)
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    log = initialize_logging('compartment volume estimation', log_dir=f_name + '/logs/')
    log.info("parameters: celltype = %s, min_comp_length = %.i" % (label_cts, min_comp_len))
    time_stamps = [time.time()]
    step_idents = ['t-0']
    log.info('Step 1/2 calculating volume estimate for axon/dendrite per cell')
    if full_cell_dict is not None:
        soma_centres = np.zeros((len(cellids), 3))
    input = [[cellid, min_comp_len, full_cell_dict[cellid], spiness] for cellid in cellids]
    morph_dicts = start_multiprocess_imap(axon_dendritic_arborization_cell, input)
    morph_dicts = np.array([morph_dicts])[0]
    axon_dicts = morph_dicts[:, 0]
    dendrite_dicts = morph_dicts[:, 1]
    nonzero_inds = axon_dicts != 0
    axon_dicts = axon_dicts[nonzero_inds]
    dendrite_dicts = dendrite_dicts[nonzero_inds]
    cellids = cellids[nonzero_inds]
    axon_length_ct = np.zeros(len(cellids))
    dendrite_length_ct = np.zeros(len(cellids))
    axon_vol_ct = np.zeros(len(cellids))
    dendrite_vol_ct = np.zeros(len(cellids))
    axon_med_radius_ct = np.zeros(len(cellids))
    dendrite_med_radius_ct = np.zeros(len(cellids))
    axon_tortuosity_complete_ct = np.zeros(len(cellids))
    dendrite_tortuosity_complete_ct = np.zeros(len(cellids))
    axon_tortuosity_sampled_ct = np.zeros(len(cellids))
    dendrite_tortuosity_sampled_ct = np.zeros(len(cellids))
    if spiness:
        spine_densities = np.zeros(len(cellids))
    for i in range(len(axon_dicts)):
        axon_dict = axon_dicts[i]
        dendrite_dict = dendrite_dicts[i]
        axon_length_ct[i] = axon_dict["length"]
        dendrite_length_ct[i] = dendrite_dict["length"]
        axon_vol_ct[i] = axon_dict["volume"]
        dendrite_vol_ct[i] = dendrite_dict["volume"]
        axon_med_radius_ct[i] = axon_dict["median radius"]
        dendrite_med_radius_ct[i] = dendrite_dict["median radius"]
        axon_tortuosity_complete_ct[i] = axon_dict["tortuosity complete"]
        dendrite_tortuosity_complete_ct[i] = dendrite_dict["tortuosity complete"]
        axon_tortuosity_sampled_ct[i] = axon_dict["tortuosity sampled"]
        dendrite_tortuosity_sampled_ct[i] = dendrite_dict["tortuosity sampled"]
        if full_cell_dict is not None:
            try:
                soma_centres[i] = full_cell_dict[cellids[i]]["soma centre"]
            except KeyError:
                all_cell_dict = load_pkl2obj("cajal/scratch/users/arother/j0251v4_prep/combined_fullcell_ax_dict.pkl")
                soma_centres[i] = all_cell_dict[cellids[i]]["soma centre"]
        if spiness:
            spine_densities[i] = dendrite_dict["spine density"]


    time_stamps.append(time.time())
    step_idents.append('calculating bounding box volume per cell')

    log.info('Step 2/2 processing and plotting ct arrays')
    ds_size = (np.array([27119, 27350, 15494]) * ssd.scaling)/ 1000 #size of whole dataset
    ds_vol = np.prod(ds_size)
    axon_vol_perc = axon_vol_ct/ds_vol * 100
    dendrite_vol_perc = dendrite_vol_ct/ds_vol * 100

    ct_vol_comp_dict = {"cell ids": cellids, "axon length": axon_length_ct,
                        "dendrite length": dendrite_length_ct,
                        "axon volume bb": axon_vol_ct, "dendrite volume bb": dendrite_vol_ct,
                        "axon volume percentage": axon_vol_perc,
                        "dendrite volume percentage": dendrite_vol_perc, "axon median radius": axon_med_radius_ct,
                        "dendrite median radius": dendrite_med_radius_ct,
                        "axon tortuosity complete": axon_tortuosity_complete_ct,
                        "dendrite tortuosity complete": dendrite_tortuosity_complete_ct,
                        "axon tortuosity sampled": axon_tortuosity_sampled_ct,
                        "dendrite tortuosity sampled": dendrite_tortuosity_sampled_ct}

    if full_cell_dict is not None:
        soma_centres = soma_centres[nonzero_inds]
        distances_between_soma = scipy.spatial.distance.cdist(soma_centres, soma_centres, metric = "euclidean") / 1000
        distances_between_soma = distances_between_soma[distances_between_soma > 0].reshape(len(cellids), len(cellids) - 1)
        avg_soma_distance_per_cell = np.mean(distances_between_soma, axis=1)
        pairwise_soma_distances = scipy.spatial.distance.pdist(soma_centres, metric = "euclidean") / 1000
        soma_centres_to_dataset_borders = np.min(np.hstack([soma_centres/1000, ds_size-soma_centres/1000]).reshape(len(soma_centres), 6), axis = 1)
        ct_vol_comp_dict["soma distance to dataset border"] = soma_centres_to_dataset_borders
        ct_vol_comp_dict["mean soma distance"] = avg_soma_distance_per_cell
    if spiness:
        ct_vol_comp_dict["spine density"] = spine_densities
    vol_comp_pd = pd.DataFrame(ct_vol_comp_dict)
    vol_comp_pd.to_csv("%s/ct_vol_comp.csv" % f_name)

    #write soma centre coords and pairwise distances into dictionary but not dataframe (different length than other parameters
    if full_cell_dict is not None:
        ct_vol_comp_dict["soma centre coords"] = soma_centres
        ct_vol_comp_dict["pairwise soma distance"] = pairwise_soma_distances

    vol_result_dict = ResultsForPlotting(celltype = label_cts, filename = f_name, dictionary = ct_vol_comp_dict)

    for key in ct_vol_comp_dict.keys():
        if "ids" in key:
            continue
        if "axon" in key:
            vol_result_dict.plot_hist(key=key, subcell="axon", bins = 10)
        elif "dendrite" in key or "spine density" in key:
            vol_result_dict.plot_hist(key = key, subcell="dendrite", bins = 10)
        elif "soma distance" in key:
            if "pairwise" in key:
                vol_result_dict.plot_hist(key=key, subcell="soma", cells=False, bins = 30)
            else:
                vol_result_dict.plot_hist(key= key, subcell="soma", bins = 10)

    write_obj2pkl("%s/ct_vol_comp.pkl" % f_name, ct_vol_comp_dict)

    time_stamps.append(time.time())
    step_idents.append('processing arrays per celltype, plotting')
    log.info("compartment volume estimation per celltype finished")

    return f_name

def compare_compartment_volume_ct(celltype1, filename, ct_dict, celltype2= None, percentile = None, filename1 = None, filename2 = None, min_comp_len = 100, label_ct1 = None, label_ct2 = None, color_key = None):
    '''
    compares estimated compartment volumes (by bounding box) between two celltypes that have been generated by axon_den_arborization_ct.
    Data will be compared in histogram and violinplots. P-Values are computed by ranksum test.
    :param celltype1: j0256: STN=0, DA=1, MSN=2, LMAN=3, HVC=4, TAN=5, GPe=6, GPi=7,
#                      FS=8, LTS=9, NGF=10
    :param celltype2: compared against celltype 2,not needed if percentiles are compared
    :param percentile: if percentile given not two celltypes but two different populations within a celltye will be compared, has to be either 49 or 51 not 50
    :param filename1, filename2: only if data preprocessed: filename were preprocessed data is stored
    :param min_comp_len: minimum comparment length used by analysis
    :return:
    '''
    if color_key == None:
        color1 = "#EAAE34"
        color2 = "#2F86A8"
    else:
        ct_colors = CelltypeColors()
        ct_palette = ct_colors.ct_palette(color_key, num=True)
        color1 = ct_palette[celltype1]
        color2 = ct_palette[celltype2]

    if percentile is None and celltype2 is None:
        raise ValueError("either celltypes or percentiles must be compared")
    if label_ct1 is None:
        ct1_str = ct_dict[celltype1]
    else:
        ct1_str = label_ct1
    if celltype2 is not None:
        if label_ct2 is None:
            ct2_str = ct_dict[celltype2]
        else:
            ct2_str = label_ct2
    if percentile is not None:
        if percentile == 50:
            raise ValueError("Due to ambiguity, value has to be either 49 or 51")
        else:
            ct1_str = ct_dict[celltype1] + " p%.2i" % percentile
            ct2_str = ct_dict[celltype1] + " p%.2i" % (100 - percentile)
    f_name = "%s/comp_compartment_%s_%s_comp_volume_mcl%i" % (
        filename, ct1_str,ct2_str, min_comp_len)
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    log = initialize_logging('compare compartment volumes between two celltypes', log_dir=f_name + '/logs/')
    log.info("parameters: celltype1 = %s,celltype2 = %s min_comp_length = %.i" % (ct1_str, ct2_str, min_comp_len))
    time_stamps = [time.time()]
    step_idents = ['t-0']
    ct1_comp_dict = load_pkl2obj("%s/ct_vol_comp.pkl"% filename1)
    ct2_comp_dict = load_pkl2obj("%s/ct_vol_comp.pkl"% filename2)
    comp_dict_keys = list(ct1_comp_dict.keys())
    if "soma centre coords" in comp_dict_keys:
        log.info("compute mean soma distance between %s and %s" % (ct1_str, ct2_str))
        ct1_soma_coords = ct1_comp_dict["soma centre coords"]
        ct2_soma_coords = ct2_comp_dict["soma centre coords"]
        ct1_distances2ct2 = scipy.spatial.distance.cdist(ct1_soma_coords, ct2_soma_coords, metric="euclidean") / 1000
        ct1avg_soma_distance2ct2_per_cell = np.mean(ct1_distances2ct2, axis=1)
        ct2_distances2ct1 = scipy.spatial.distance.cdist(ct2_soma_coords, ct1_soma_coords,
                                                         metric="euclidean") / 1000
        ct2avg_soma_distance2ct1_per_cell = np.mean(ct2_distances2ct1, axis=1)
        ct_soma_coords = np.concatenate((ct1_soma_coords, ct2_soma_coords))
        pairwise_distances_cts = scipy.spatial.distance.pdist(ct_soma_coords, metric = "euclidean") / 1000
        ct1_comp_dict["avg soma distance to other celltype"] = ct1avg_soma_distance2ct2_per_cell
        ct2_comp_dict["avg soma distance to other celltype"] = ct2avg_soma_distance2ct1_per_cell
        ct1_comp_dict["pairwise soma distance to other celltype"] = pairwise_distances_cts
        ct2_comp_dict["pairwise_soma distance to other celltype"] = pairwise_distances_cts
        ct1_comp_dict.pop("soma centre coords")
        ct2_comp_dict.pop("soma centre coords")
        comp_dict_keys = list(ct1_comp_dict.keys())
    log.info("compute statistics for comparison, create violinplot and histogram")
    ranksum_results = pd.DataFrame(columns=comp_dict_keys[1:], index=["stats", "p value"])
    results_comparision = ComparingResultsForPLotting(celltype1=ct1_str,
                                                      celltype2=ct2_str, filename=f_name,
                                                      dictionary1=ct1_comp_dict, dictionary2=ct2_comp_dict,
                                                      color1=color1,
                                                      color2=color2)
    for key in ct1_comp_dict.keys():
        if "ids" in key or ("pairwise" in key and "other" in key):
            continue
        #calculate p_value for parameter
        stats, p_value = ranksums(ct1_comp_dict[key], ct2_comp_dict[key])
        ranksum_results.loc["stats", key] = stats
        ranksum_results.loc["p value", key] = p_value
        #plot parameter as violinplot
        if "axon" in key:
            subcell = "axon"
        elif "dendrite" in key:
            subcell = "dendrite"
        else:
            subcell = "soma"
        if "pairwise" in key:
            column_labels = ["distances within %s" % ct1_str, "distances within %s" % ct2_str, "distances between %s and %s" % (ct1_str, ct2_str)]
            results_for_plotting = results_comparision.result_df_per_param(key, key2 = "pairwise soma distance to other celltype", column_labels= column_labels)
            s1, p1 = ranksums(ct1_comp_dict[key], ct1_comp_dict["pairwise soma distance to other celltype"])
            s2, p2 = ranksums(ct2_comp_dict[key], ct1_comp_dict["pairwise soma distance to other celltype"])
            ranksum_results.loc["stats", "pairwise among %s to mixed" % ct1_str] = s1
            ranksum_results.loc["p value", "pairwise among %s to mixed" % ct1_str] = p1
            ranksum_results.loc["stats", "pairwise among %s to mixed" % ct2_str] = s2
            ranksum_results.loc["p value", "pairwise among %s to mixed" % ct2_str] = p2
            ptitle = "pairwise soma distances within and between %s and %s" % (ct1_str, ct2_str)
            palette = {f'distances within {ct1_str}': color1, f'distances within {ct2_str}': color2,
                       f'distances between {ct1_str} and {ct2_str}': 'gray'}
            results_comparision.plot_hist_comparison(key, result_df= results_for_plotting, subcell=subcell, cells=False, title=ptitle, norm_hist=False, palette=palette)
            results_comparision.plot_hist_comparison(key, result_df= results_for_plotting, subcell=subcell,
                                                     cells=False, title=ptitle, norm_hist=True, palette=palette)
        else:
            results_for_plotting = results_comparision.result_df_per_param(key)
            results_comparision.plot_hist_comparison(key, result_df= results_for_plotting, subcell=subcell, bins=10, norm_hist=False)
            results_comparision.plot_hist_comparison(key, result_df= results_for_plotting, subcell=subcell, bins=10, norm_hist=True)
            results_comparision.plot_violin(key, results_for_plotting, subcell, stripplot=True)
            results_comparision.plot_box(key, results_for_plotting, subcell, stripplot=False)


    ranksum_results.to_csv("%s/ranksum_%s_%s.csv" % (f_name,ct1_str,ct2_str))

    time_stamps.append(time.time())
    step_idents.append('comparing celltypes')
    log.info("compartment volume comparison finished")

def compare_compartment_volume_ct_multiple(celltypes, filename, ct_dict, filename_cts = None, min_comp_len = 100, label_cts = None, colours = None):
    '''
    compares estimated compartment volumes (by bounding box) between multiple celltypes that have been generated by axon_den_arborization_ct.
    If only two, use compare_compartment_volume_ct.
    Data will be compared in histogram and violinplots. P-Values are computed by ranksum test.
    :param celltypes: j0256: STN=0, DA=1, MSN=2, LMAN=3, HVC=4, TAN=5, GPe=6, GPi=7,
#                      FS=8, LTS=9, NGF=10, list or array of celltypes to be compared. If subpopulations from same celltype,
                    length must match label_cts and filenames, repeat celltype then.
    :param percentile: if percentile given not two celltypes but two different populations within a celltye will be compared, has to be either 49 or 51 not 50
    :param filename_cts: only if data preprocessed: filenames were preprocessed data is stored, must be sam elength as celltypes
    :param min_comp_len: minimum comparment length used by analysis
    :param label_cts: labels for celltypes for e.g. subpopulations. If None use from ct_dict
    :param colours: list of colours to use for plotting
    :return:
    '''
    amount_celltypes = len(celltypes)
    if label_cts is None:
        label_cts = [ct_dict[celltypes[i]] for i in range(amount_celltypes)]
    f_name = "%s/comp_compartment_%s_%s_comp_volume_mcl%i" % (
        filename, label_cts[0], label_cts[1], min_comp_len)
    if not os.path.exists(f_name):
        os.mkdir(f_name)
    log = initialize_logging('compare compartment volumes between two celltypes', log_dir=f_name + '/logs/')
    log.info("parameters: celltype1 = %s,celltype2 = %s, amount celltypes = %i, min_comp_length = %.i" % (label_cts[0], label_cts[1], amount_celltypes, min_comp_len))
    time_stamps = [time.time()]
    step_idents = ['t-0']
    ct_comp_dicts = [load_pkl2obj("%s/ct_vol_comp.pkl"% filename_cts[i]) for i in range(amount_celltypes)]
    comp_dict_keys = list(ct_comp_dicts[0].keys())
    if colours is None:
        blues = ["#0ECCEB", "#0A95AB", "#06535F", "#065E6C", "#043C45"]
        colours = blues[:amount_celltypes]
    if "soma centre coords" in comp_dict_keys:
        for i in range(amount_celltypes):
            for j in range(1, amount_celltypes):
                if i >= j:
                    continue
                log.info("compute mean soma distance between %s and %s" % (label_cts[i], label_cts[j]))
                ct1_soma_coords = ct_comp_dicts[i]["soma centre coords"]
                ct2_soma_coords = ct_comp_dicts[j]["soma centre coords"]
                ct1_distances2ct2 = scipy.spatial.distance.cdist(ct1_soma_coords, ct2_soma_coords, metric="euclidean") / 1000
                ct1avg_soma_distance2ct2_per_cell = np.mean(ct1_distances2ct2, axis=1)
                ct2_distances2ct1 = scipy.spatial.distance.cdist(ct2_soma_coords, ct1_soma_coords,
                                                                 metric="euclidean") / 1000
                ct2avg_soma_distance2ct1_per_cell = np.mean(ct2_distances2ct1, axis=1)
                ct_soma_coords = np.concatenate((ct1_soma_coords, ct2_soma_coords))
                pairwise_distances_cts = scipy.spatial.distance.pdist(ct_soma_coords, metric = "euclidean") / 1000
                ct_comp_dicts[i]["avg soma distance to %s" % label_cts[j]] = ct1avg_soma_distance2ct2_per_cell
                ct_comp_dicts[j]["avg soma distance to %s" % label_cts[i]] = ct2avg_soma_distance2ct1_per_cell
                ct_comp_dicts[i]["pairwise soma distance to %s" % label_cts[i]] = pairwise_distances_cts
                ct_comp_dicts[j]["pairwise_soma distance to %s" % label_cts[j]] = pairwise_distances_cts

    log.info("compute statistics for comparison, create violinplot and histogram")
    ranksum_results = pd.DataFrame()
    results_comparison = ComparingMultipleForPLotting(ct_list = label_cts, filename = f_name, dictionary_list = ct_comp_dicts, colour_list = colours)
    for key in comp_dict_keys:
        if "ids" in key or "soma centre coords" in key or "tortuosity" in key:
            continue
        #calculate p_value for parameter
        for i in range(amount_celltypes):
            for j in range(1, amount_celltypes):
                if i >= j:
                    continue
                stats, p_value = ranksums(ct_comp_dicts[i][key], ct_comp_dicts[j][key])
                ranksum_results.loc["stats " + key, label_cts[i] + " vs " + label_cts[j]] = stats
                ranksum_results.loc["p value " + key, label_cts[i] + " vs " + label_cts[j]] = p_value
        #plot parameter as violinplot
        if "axon" in key:
            subcell = "axon"
        elif "dendrite" in key:
            subcell = "dendrite"
        else:
            subcell = "soma"
        if "pairwise" in key and "to" in key:
            celltype_distancedto = key.split[-1]
            ct_distanceto_ind = np.where(label_cts == celltype_distancedto)[0]
            column_labels = label_cts.remove(celltype_distancedto)
            dict_lengths = np.array([len(ct_comp_dicts[i][key]) for i in range(amount_celltypes) if i != ct_distanceto_ind])
            max_length = np.max(dict_lengths)
            results_for_plotting = pd.DataFrame(columns = column_labels, index = range(max_length))
            for i in range(amount_celltypes):
                if i == ct_distanceto_ind:
                    continue
                results_for_plotting.loc[0:len(ct_comp_dicts[i][key]) - 1, label_cts[i]] = \
                ct_comp_dicts[i][key]
            results_comparison.plot_hist_comparison(key, subcell, results_for_plotting, bins=10, norm_hist=False)
            results_comparison.plot_hist_comparison(key, subcell, results_for_plotting, bins=10, norm_hist=True)
            results_comparison.plot_violin(key, results_for_plotting, subcell, stripplot=True)
            results_comparison.plot_box(key, results_for_plotting, subcell, stripplot=False)
        else:
            results_for_plotting = results_comparison.result_df_per_param(key)
            results_comparison.plot_hist_comparison(key, subcell, result_df= results_for_plotting, bins=10, norm_hist=False)
            results_comparison.plot_hist_comparison(key, subcell, result_df= results_for_plotting, bins=10, norm_hist=True)
            results_comparison.plot_violin(key, results_for_plotting, subcell, stripplot=True)
            results_comparison.plot_box(key, results_for_plotting, subcell, stripplot=False)


    ranksum_results.to_csv("%s/ranksum_%s_%s.csv" % (f_name,label_cts[0], label_cts[1]))
    time_stamps.append(time.time())
    step_idents.append('comparing celltypes')
    log.info("compartment volume comparison finished")

def compare_soma_diameters(cellids, celltypes, filename, colours = None, use_skel = False):
    '''
    Compares different groups soma diameter by estimating it with get_soma_diameter,
    running a ranksum test from scipy.stats and plotting it. Functions assumes cells are already prefiltered.
    :param cellids: array or list cellids of the different cells, grouped by celltype
    :param celltypes: labels or celltypes of the groups to be compared, assumes str
    :param filename: filename where results should be saved
    :param colors: colors for plotting, if None will be different shades of blue
    :param use_skel: if True uses skeleton node predictions to get mesh from soma
                    otherwise uses vertex label dict (more exact)
    :return:
    '''
    num_cts = len(celltypes)
    f_name = f'{filename}/soma_diameter_comparison/'
    log = initialize_logging('soma diameter comparison', log_dir=f_name + '/logs/')
    all_cellids = np.hstack(cellids)
    log.info(f'Compare {len(all_cellids)} of {num_cts} groups/ celltypes: {celltypes}')
    if use_skel:
        log.info('use skeleton node predictions to get soma mesh coordinates')
    else:
        log.info('use vertex label dict predictions to get soma vertices')
    ct_dict = {i: ct for i, ct in enumerate(celltypes)}
    if colours is None:
        blues = ["#0ECCEB", "#0A95AB", "#06535F", "#065E6C", "#043C45"]
        colours = blues[num_cts]

    log.info(f'Step 1/3: Get soma diameter for {len(all_cellids)} cells')
    all_cts = []
    for i in range(num_cts):
        ct_str = ct_dict[i]
        all_cts.append([ct_str for i in range(len(cellids[i]))])
    all_cts = np.hstack(all_cts)
    columns = ['cellid', 'celltype', 'soma diameter [µm]']
    soma_results_df = pd.DataFrame(columns=columns, index = range(len(all_cellids)))
    soma_results_df['cellid'] = all_cellids
    soma_results_df['celltype'] = all_cts
    #get soma centre coords, soma radius in µm
    soma_output = start_multiprocess_imap(get_cell_soma_radius, all_cellids)
    soma_output = np.array(soma_output, dtype='object')
    soma_radius = soma_output[:, 1].astype(float)
    soma_diameter = soma_radius * 2
    soma_results_df['soma diameter [µm]'] = soma_diameter
    len_before_drop = len(soma_results_df)
    cellids_before_drop = soma_results_df['cellid']
    soma_results_df = soma_results_df.dropna()
    len_after_drop = len(soma_results_df)
    cellids_after_drop = soma_results_df['cellid']
    cellids_no_soma = cellids_before_drop[np.in1d(cellids_before_drop, cellids_after_drop) == False]
    soma_results_df.to_csv(f'{f_name}/soma_diameter_results.csv')
    log.info(f'{len_before_drop - len_after_drop} cells (cellids: {cellids_no_soma}) were excluded due to missing soma skeleton points.')

    log.info('Step 2/3: Plot results')
    ct_palette = {celltypes[i]: colours[i] for i in range(num_cts)}
    title = 'soma diameter comparison'
    sns.stripplot(x='celltype', y='soma diameter [µm]', data=soma_results_df, color='black', alpha=0.2,
                  dodge=True, size=2)
    sns.violinplot(x='celltype', y='soma diameter [µm]', data=soma_results_df, inner="box",
                   palette=ct_palette)
    plt.title(title)
    plt.savefig(f'{f_name}/soma_diameter_celltypes_violin.png')
    plt.savefig(f'{f_name}/soma_diameter_celltypes_violin.svg')
    plt.close()
    sns.boxplot(x='celltype', y='soma diameter [µm]', data=soma_results_df, palette=ct_palette)
    plt.title(title)
    plt.savefig(f'{f_name}/soma_diameter_celltypes_box.png')
    plt.savefig(f'{f_name}/soma_diameter_celltypes_box.svg')
    plt.close()
    sns.histplot(x = 'soma diameter [µm]', data = soma_results_df, hue = 'celltype',
                 palette=ct_palette, common_norm=False, fill=False,
                 element="step", legend = True,linewidth = 3)
    plt.ylabel('count of cells')
    plt.title(title)
    plt.savefig(f'{f_name}/soma_diameter_celltypes_hist.png')
    plt.savefig(f'{f_name}/soma_diameter_celltypes_hist.svg')
    plt.close()
    sns.histplot(x='soma diameter [µm]', data=soma_results_df, hue='celltype',
                 palette=ct_palette, common_norm=True, fill=False,
                 element="step", legend=True, linewidth=3)
    plt.ylabel('fraction of cells')
    plt.title(title)
    plt.savefig(f'{f_name}/soma_diameter_celltypes_hist_norm.png')
    plt.savefig(f'{f_name}/soma_diameter_celltypes_hist_norm.svg')
    plt.close()

    log.info('Step 3/3: Calculate statistics and plot results')
    celltype_diameter_groups = [group['soma diameter [µm]'].values for name, group in soma_results_df.groupby('celltype')]
    ind_celltypes_mapped = {ct: i for i, ct in enumerate(celltypes)}
    celltype_groups = soma_results_df.groupby('celltype')
    celltype_diameter_median = celltype_groups['soma diameter [µm]'].median()
    celltype_diameter_median.to_csv(f'{f_name}/median_diameters_celltype.csv')
    # run kruskal wallis test
    kruskal_results = kruskal(*celltype_diameter_groups)
    log.info(f'Results of kruskal-wallis-test: p-value = {kruskal_results[1]:.2f}, stats: {kruskal_results[0]:.2f}')
    # run ranksum test on each combination
    celltype_combs = combinations(celltypes, 2)
    comb_list = list(celltype_combs)
    comb_list_str = [f'{ct1} vs {ct2}' for (ct1, ct2) in comb_list]
    ranksum_results = pd.DataFrame(columns=comb_list_str, index=['stats', 'p-value'])
    for comb in comb_list:
        ct1 = comb[0]
        ct2 = comb[1]
        ct1_data = celltype_diameter_groups[ind_celltypes_mapped[ct1]]
        ct2_data = celltype_diameter_groups[ind_celltypes_mapped[ct2]]
        stats, p_value = ranksums(ct1_data, ct2_data)
        ranksum_results.loc['stats', f'{ct1} vs {ct2}'] = stats
        ranksum_results.loc['p-value', f'{ct1} vs {ct2}'] = p_value
    ranksum_results.to_csv(f'{f_name}/diameter_ranksum_results.csv')

    log.info('Comparison of soma diameters finished.')




