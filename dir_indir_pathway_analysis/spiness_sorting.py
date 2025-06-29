
import numpy as np
import pandas as pd
import os as os
import time
from syconn.handler.config import initialize_logging
from syconn.handler.basics import load_pkl2obj
from tqdm import tqdm
from syconn.handler.basics import write_obj2pkl
from cajal.nvmescratch.users.arother.bio_analysis.general.analysis_morph_helper import get_spine_density
from cajal.nvmescratch.users.arother.bio_analysis.general.result_helper import ComparingResultsForPLotting
from multiprocessing import pool
from scipy.stats import ranksums
from functools import partial

def saving_spiness_percentiles(ssd, celltype, filename_saving, analysis_params, filename_plotting = None, full_cells = True, percentiles = [], min_comp_len = 100):
    """
    saves MSN IDS depending on their spiness. Spiness is determined via spiness skeleton nodes using counting_spiness as spine density in relation to the skeelton length
    of the dendrite. Cells without a minimal compartment length are discarded.
    :param ssd: super segmentation dataset
    :param celltype: ssd = SuperSegmentationDataset(working_dir=global_params.config.working_dir)
    :param filename_saving: directory where cells should be saved
    :param analysis_params: object with saved file locations etc
    :param full_cells: if True, cellids of preprocessed cells with axon, dendrite, soma are loaded
    :param percentiles: list of percentiles, that should be saved
    :param min_comp_len: minimal compartment length in µm
    :return:
    """
    start = time.time()
    ct_dict = analysis_params.ct_dict(with_glia=False)
    if not os.path.exists(filename_saving):
        os.mkdir(filename_saving)
    if not filename_plotting:
        filename_plotting = filename_saving
    log = initialize_logging('sorting cellids according to spiness', log_dir=filename_plotting + '/logs/')
    log.info(
        "parameters: celltype = %s, min_comp_length = %.i" %
        (ct_dict[celltype], min_comp_len))
    time_stamps = [time.time()]
    step_idents = ['t-0']
    if full_cells:
        cellids = analysis_params.load_full_cell_array(celltype)
        try:
            full_cell_dict = analysis_params.load_cell_dict(celltype)
            length_dicts = True
        except FileNotFoundError:
            length_dicts = False
    else:
        cellids = ssd.ssv_ids[ssd.load_numpy_data("celltype_cnn_e3") == celltype]

    known_mergers = analysis_params.load_known_mergers()
    misclassified_astro_ids = analysis_params.load_potential_astros()
    merger_inds = np.in1d(cellids, known_mergers) == False
    cellids = cellids[merger_inds]
    astro_inds = np.in1d(cellids, misclassified_astro_ids) == False
    cellids = cellids[astro_inds]

    log.info("Step 1/2: iterate over cells and get amount of spines")
    p = pool.Pool()
    if length_dicts:
        spine_densities = p.map(partial(get_spine_density, min_comp_len = min_comp_len, full_cell_dict = full_cell_dict), tqdm(cellids))
    else:
        spine_densities = p.map(partial(get_spine_density, min_comp_len=min_comp_len),
                                tqdm(cellids))
    spine_densities = np.array(spine_densities)
    spine_inds = spine_densities > 0
    spine_densities = spine_densities[spine_inds]
    cellids = cellids[spine_inds]
    spinetime = time.time() - start
    print("%.2f sec for iterating through %s cells" % (spinetime, ct_dict[celltype]))
    time_stamps.append(time.time())
    step_idents.append('iterating over %s cells' % ct_dict[celltype])

    log.info("Step 2/2 sort into percentiles")
    if filename_plotting is not None:
        ranksum_results = pd.DataFrame(columns=percentiles, index=["stats", "p value"])

    for percentile in percentiles:
        perc_low = np.percentile(spine_densities, percentile, interpolation="higher")
        perc_low_inds = np.where(spine_densities < perc_low)[0]
        perc_high = np.percentile(spine_densities, 100 - percentile, interpolation="lower")
        perc_high_inds = np.where(spine_densities > perc_high)[0]
        cellids_low = cellids[perc_low_inds]
        cellids_high = cellids[perc_high_inds]
        if percentile == 50:
            percentile = percentile - 1
        write_obj2pkl("%s/full_%3s p%.2i_arr_c%i.pkl" % (filename_saving, ct_dict[celltype], percentile, min_comp_len), cellids_low)
        write_obj2pkl("%s/full_%3s p%.2i_arr_c%i.pkl" % (filename_saving, ct_dict[celltype], 100 - percentile, min_comp_len), cellids_high)
        spine_amount_dict_low = {cellid: spine_amount for cellid, spine_amount in zip(cellids_low, spine_densities[perc_low_inds])}
        spine_amount_dict_high = {cellid: spine_amount for cellid, spine_amount in
                                 zip(cellids_high, spine_densities[perc_high_inds])}
        write_obj2pkl("%s/full_%3s_spine_dict_%i_%i.pkl" % (filename_saving, ct_dict[celltype], percentile, min_comp_len), spine_amount_dict_low)
        write_obj2pkl("%s/full_%3s_spine_dict_%i_%i.pkl" % (filename_saving, ct_dict[celltype], 100 - percentile, min_comp_len),
                      spine_amount_dict_high)
        ct1_str = ct_dict[celltype] + " p%.2i" % percentile
        ct2_str = ct_dict[celltype] + " p%.2i" % (100 - percentile)
        if filename_plotting is not None:
            spine_amount_results_low = {"spine density": spine_densities[perc_low_inds], "cellids": cellids_low}
            spine_amount_results_high = {"spine density": spine_densities[perc_high_inds], "cellids": cellids_high}
            spine_amount_results = ComparingResultsForPLotting(celltype1 = ct1_str, celltype2 = ct2_str, filename = filename_plotting, dictionary1 = spine_amount_results_low, dictionary2 = spine_amount_results_high, color1 = "gray", color2 = "darkturquoise")
            spine_amount_results.plot_hist_comparison(key = "spine density", subcell = "spine", bins = 10, norm_hist=False)
            spine_amount_results.plot_hist_comparison(key = "spine density", subcell = "spine", bins = 10, norm_hist=True)
            spine_results_df = spine_amount_results.result_df_per_param(key = "spine density")
            spine_amount_results.plot_violin(key = "spine density", result_df=spine_results_df, subcell = "spine")
            sum_cellids = len(cellids_low) + len(cellids_high)
            spine_results_df_full = pd.DataFrame(columns = ["cellids", "spine density" ,"percentile"], index = range(sum_cellids))
            spine_results_df_full.loc[0: len(cellids_low) - 1, "cellids"] = cellids_low
            spine_results_df_full.loc[0: len(cellids_low) - 1, "percentile"] = percentile
            spine_results_df_full.loc[0: len(cellids_low) - 1, "spine density"] = spine_amount_results_low["spine density"]
            spine_results_df_full.loc[len(cellids_low): sum_cellids - 1, "cellids"] = cellids_high
            spine_results_df_full.loc[len(cellids_low): sum_cellids- 1, "percentile"] = 100 - percentile
            spine_results_df_full.loc[len(cellids_low): sum_cellids - 1, "spine density"] = spine_amount_results_high[
                "spine density"]
            spine_results_df_full.to_csv("%s/spine_densities_%s_%i_%i.csv" % (filename_plotting, ct_dict[celltype], percentile, min_comp_len))
            stats, p_value = ranksums(spine_amount_results_low["spine density"], spine_amount_results_high["spine density"])
            ranksum_results.loc["stats", percentile] = stats
            ranksum_results.loc["p value", percentile] = p_value

    if filename_plotting is not None:
        ranksum_results.to_csv("%s/ranksum_results_%s_%i.csv" % (filename_plotting, ct_dict[celltype], min_comp_len))



    perctime = time.time() - spinetime
    print("%.2f sec for creating percentile arrays" % perctime)
    time_stamps.append(time.time())
    step_idents.append('creating and saving percentile arrays')
    log.info("Analysis finished")





