#TO DO: write object for results dictionary to standardize plotting of results
#put all relevant function here in this helper file
#make possibility for 2 or more different color schemmes
#boxplot, violinplot, histogram (normed, not normed), scatterplot
#also add flowchart, networx plot
#one for single dictionary and one for comparing results from two dictionaries

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.patches

class ResultsForPlotting():
    """
    this class contains a dictionary with different results.
    """

    def __init__(self, celltype, filename,dictionary, color = "black"):
        if type(dictionary) != dict:
            raise ValueError("must be dictionary")
        self.celltype = celltype
        self.filename = filename
        self.dictionary = dictionary
        self.color = color

    def param_label(self, key, subcell):
        """
        specifies the label for x or y-axis based on the key and subcellular compartment.
        :param key: parameter as key in dictionary
        :param subcell: subcellular compartment
        :return: param_label
        """
        if "density" in key:
            if "volume" in key:
                param_label = "%s volume density [µm³/µm]" % subcell
            elif "size" in key and subcell == "synapse":
                param_label = "%s size density [µm²/µm]" % subcell
            elif "length" in key:
                param_label = "%s length density [µm/µm]" % subcell
            else:
                param_label = "%s density per µm" % subcell
        else:
            if "number" in key:
                if "percentage" in key:
                    param_label = "percentage of %ss" % subcell
                elif "pathlength" in key:
                    param_label = "number %s per µm" % subcell
                elif "surface" in key:
                    param_label = "number %s per surface area [1/µm²]" % subcell
                else:
                    param_label = "number of %ss" % subcell
            elif "size" in key:
                if "percentage" in key:
                    param_label = "percentage of %s size" % subcell
                else:
                    if subcell == "synapse":
                        if "average" in key:
                            param_label = "average %s size [µm²]" % subcell
                        elif "pathlength" in key:
                            param_label = "sum size synapses per pathlength [µm²/µm]"
                        elif "surface" in key:
                            param_label = "sum size synapses per surface area [µm²/µm²]"
                        else:
                            param_label = "%s size [µm²]" % subcell
            elif "length" in key:
                param_label = "pathlength in µm"
            elif "vol" in key:
                if "percentage" in key:
                    param_label = "% of whole dataset"
                else:
                    param_label = " %s volume in µm³" % subcell
            elif "distance" in key:
                param_label = "distance in µm"
            elif "median radius" in key:
                param_label = "median radius in µm"
            elif "tortuosity" in key:
                param_label = "%s tortuosity" % subcell
            elif "fraction" in key:
                param_label = "fraction of %s" % subcell
            else:
                param_label = key
        return param_label

    def plot_hist(self, key, subcell, cells = True, norm_hist = False, bins = None, xlabel = None, celltype2 = None, outgoing = False, logscale = False):
        """
        plots array given with key in histogram plot
        :param key: key of dictionary that should be plotted
        :param subcell: compartment or subcellular structure that will be plotted
        :param cells: True: cells are plotted, False: subcellular structures are plotted
        :param color: color for plotting
        :param norm_hist: if true: histogram will be normed
        :param bins: number of bins
        :param xlabel: label of x axis, not needed if clear from key
        :param celltype2: second celltype, if connectivty towards another celltype is tested
        :param outgoing: if connectivity is analysed, if True then self.celltype is presynaptic
        :return:
        """
        if bins is None:
            bins = "auto"
        if norm_hist:
            if logscale:
                sns.histplot(self.dictionary[key], fill=False, element="step", bins=bins, common_norm=True, legend=True,
                             color = self.color, linewidth = 3, log_scale=True)
            else:
                sns.histplot(self.dictionary[key], fill=False, element="step", bins=bins, common_norm=True, legend=True,
                             color=self.color, linewidth=3, log_scale=False)
            if cells:
                plt.ylabel("fraction of cells")
            else:
                plt.ylabel("fraction of %s" % subcell)
        else:
            if logscale:
                sns.histplot(self.dictionary[key], fill=False, element="step", bins=bins, common_norm=False, legend=True,
                             color=self.color, linewidth = 3, log_scale=True)
            else:
                sns.histplot(self.dictionary[key], fill=False, element="step", bins=bins, common_norm=False,
                             legend=True,
                             color=self.color, linewidth=3, log_scale=False)
            if cells:
                plt.ylabel("count of cells")
            else:
                plt.ylabel("count of %s" % subcell)
        if xlabel:
            plt.xlabel(xlabel)
        else:
            plt.xlabel(self.param_label(key, subcell))
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if celltype2:
            if outgoing:
                plt.title("%s from %s to %s" % (key, self.celltype, celltype2))
                if norm_hist:
                    if logscale:
                        plt.savefig("%s/%s_%s2%s_hist_norm_log.svg" % (self.filename, key, self.celltype, celltype2))
                    else:
                        plt.savefig("%s/%s_%s2%s_hist_norm.svg" % (self.filename, key, self.celltype, celltype2))
                else:
                    if logscale:
                        plt.savefig("%s/%s_%s2%s_hist_log.svg" % (self.filename, key, self.celltype, celltype2))
                    else:
                        plt.savefig("%s/%s_%s2%s_hist.svg" % (self.filename, key, self.celltype, celltype2))
            else:
                plt.title("%s from %s to %s" % (key, celltype2, self.celltype))
                if norm_hist:
                    if logscale:
                        plt.savefig("%s/%s_%s2%s_hist_norm_log.svg" % (self.filename, key, celltype2, self.celltype))
                    else:
                        plt.savefig("%s/%s_%s2%s_hist_norm.svg" % (self.filename, key, celltype2, self.celltype))
                else:
                    if logscale:
                        plt.savefig("%s/%s_%s2%s_hist_log.svg" % (self.filename, key, celltype2, self.celltype))
                    else:
                        plt.savefig("%s/%s_%s2%s_hist.svg" % (self.filename, key, celltype2, self.celltype))
        else:
            plt.title("%s in %s %s" % (key, self.celltype, subcell))
            if norm_hist:
                if logscale:
                    plt.savefig("%s/%s%_s_%s_hist_norm_log.svg" % (self.filename, subcell, key, self.celltype))
                else:
                    plt.savefig("%s/%s%_s_%s_hist_norm.svg" % (self.filename, subcell, key, self.celltype))
            else:
                if logscale:
                    plt.savefig("%s/%s_%s_%s_hist_log.svg" % (self.filename, subcell, key, self.celltype))
                else:
                    plt.savefig("%s/%s_%s_%s_hist.svg" % (self.filename, subcell, key, self.celltype))
        plt.close()

    def multiple_param_labels(self, labels, ticks):
        self.m_labels = labels
        self.m_ticks = ticks

    def plot_violin_params(self, key, param_list,subcell, xlabel = None, ticks = None, stripplot = True, celltype2 = None, outgoing = False):
        sns.violinplot(data=param_list, inner="box")
        if stripplot:
            sns.stripplot(data=param_list, palette='dark:black', alpha=0.2, size=2)
        if xlabel:
            if ticks is None:
                raise ValueError("need labels and ticks")
            plt.xticks(ticks = ticks, labels= xlabel)
        else:
            plt.xticks(ticks=self.m_ticks, labels=self.m_labels)
        plt.ylabel(self.param_label(key, subcell))
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if celltype2:
            if outgoing:
                plt.title("%s from %s to %s" % (key, self.celltype, celltype2))
                plt.savefig("%s/%s_%s_2_%s_violin.svg" % (self.filename, key, self.celltype, celltype2))
            else:
                plt.title("%s from %s to %s" % (key, celltype2, self.celltype))
                plt.savefig("%s/%s_%s_2_%s_violin.svg" % (self.filename, key, celltype2, self.celltype))
        else:
            plt.title("%s in %s %s" % (key, self.celltype, subcell))
            plt.savefig("%s/%s_%s_%s_violin.svg" % (self.filename, key, subcell, self.celltype))
        plt.close()

    def plot_box_params(self, key, param_list,subcell, xlabel = None, ticks = None, stripplot = True, celltype2 = None, outgoing = False):
        sns.violinplot(data=param_list, inner="box")
        if stripplot:
            sns.stripplot(data=param_list, palette='dark:black', alpha=0.2, size = 2)
        if xlabel:
            if ticks is None:
                raise ValueError("need labels and ticks")
            plt.xticks(ticks = ticks, labels= xlabel)
        else:
            plt.xticks(ticks=self.m_ticks, labels=self.m_labels)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.ylabel(self.param_label(key, subcell))
        if celltype2:
            if outgoing:
                plt.title("%s from %s to %s" % (key, self.celltype, celltype2))
                plt.savefig("%s/%s_%s_2_%s_box.svg" % (self.filename, key, self.celltype, celltype2))
            else:
                plt.title("%s from %s to %s" % (key, celltype2, self.celltype))
                plt.savefig("%s/%s_%s_2_%s_box.svg" % (self.filename, key, celltype2, self.celltype))
        else:
            plt.title("%s in %s %s" % (key, self.celltype, subcell))
            plt.savefig("%s/%s_%s_%s_box.svg" % (self.filename, key, subcell, self.celltype))
        plt.close()

    def plot_bar(self, key, x, results_df, conn_celltype=None, outgoing=False):
        """
        creates box plot with more than one parameter. Dataframe with results oat least two parameter is required
        :param key: parameter to be plotted on y axis
        :param x: dataframe column on x axis
        :param hue: dataframe column acting as hue
        :param results_df: datafram, suitable one can be created with results_df_two_params
        :param stripplot: if True creates stripplot overlay
        :param conn_celltype: if third celltype connectivty is analysed
        :param outgoing: if true, connected_ct is post_synapse
        :return: None
        """
        sns.barplot(x=x, y=key, data=results_df, color=self.color)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if conn_celltype:
            if outgoing:
                plt.title('%s, %s to %s' % (key, self.celltype, conn_celltype))
                plt.savefig("%s/%s_%s_%s_2_%s_bar.svg" % (
                    self.filename, key, x, self.celltype, conn_celltype))
            else:
                plt.title('%s, %s to %s' % (key, conn_celltype, self.celltype))
                plt.savefig("%s/%s_%s_%s_2_%s_bar.svg" % (
                    self.filename, key, x, conn_celltype, self.celltype))
        else:
            plt.title('%s, %s' % (key, self.celltype))
            plt.savefig("%s/%s_%s_%s_bar.svg" % (self.filename, key,x, self.celltype))
        plt.close()


class ComparingResultsForPLotting(ResultsForPlotting):
    """
    makes plots from two dictionaries with the same keys to compare their results.
    """
    def __init__(self, celltype1, celltype2, filename, dictionary1, dictionary2, color1 = "#592A87", color2 = "#2AC644"):
        super().__init__(celltype1, filename, dictionary1)
        self.celltype1 = celltype1
        self.celltype2 = celltype2
        self.dictionary1 = dictionary1
        self.dictionary2 = dictionary2
        self.color1 = color1
        self.color2 = color2
        try:
            self.max_length_df = np.max(np.array(
                [len(self.dictionary1[list(self.dictionary1.keys())[0]]), len(self.dictionary2[list(self.dictionary2.keys())[0]])]))
        except TypeError:
            if type(self.dictionary1[list(self.dictionary1.keys())[0]]) == int and type(self.dictionary2[list(self.dictionary2.keys())[0]]) == int:
                self.max_length_df = 1
            else:
                TypeError("unknown dictionary entry")
        self.color_palette = {celltype1: color1, celltype2: color2}

    def plot_hist_comparison(self, key, result_df, subcell, cells = True, norm_hist = False, bins = None, xlabel = None, title = None, conn_celltype = None, outgoing = False, palette = None):
        """
                 plots two arrays and compares them in histogram and saves it.
                 :param key: key of dictionary that should be plotted
                 :param subcell: compartment or subcellular structure that will be plotted
                 :param cells: True: cells are plotted, False: subcellular structures are plotted
                 :param norm_hist: if true: histogram will be normed
                 :param bins: number of bins
                 :param xlabel: label of x axis, not needed if clear from key
                 :param conn_celltype: third celltype if connectivity to other celltype is tested
                 :param outgoing: if connectivity is analysed, if True then self.celltype1 and self.celltype2 are presynaptic
                 :return: None
                 """
        if bins is None:
            bins = "auto"
        if palette is None:
            palette = self.color_palette
        if norm_hist:
            sns.histplot(result_df, fill=False,element="step", bins = bins, common_norm=True, legend = True,
                         palette=palette, linewidth = 3)
            #sns.displot(self.dictionary2[key],
            #             hist_kws={"histtype": "step", "linewidth": 3, "alpha": 1, "color": self.color2},
            #             kde=False, norm_hist=True, bins=bins, label=self.celltype2)
            if cells:
                plt.ylabel("fraction of cells")
            elif "pair" in key:
                plt.ylabel("fraction of %s pairs" % subcell)
            else:
                plt.ylabel("fraction of %s" % subcell)
        else:
            sns.histplot(result_df, fill=False, element="step", bins=bins, common_norm=False, legend=True,
                         palette=palette, linewidth = 3)
            if cells:
                plt.ylabel("count of cells")
            elif "pair" in key:
                plt.ylabel("count of %s pairs" % subcell)
            else:
                plt.ylabel("count of %s" % subcell)
        plt.xticks(fontsize = 20)
        plt.yticks(fontsize = 20)
        if xlabel:
            plt.xlabel(xlabel)
        else:
            plt.xlabel(self.param_label(key, subcell))
        if conn_celltype:
            if outgoing:
                if title:
                    plt.title(title)
                else:
                    plt.title("%s from %s, %s to %s" % (key, self.celltype1, self.celltype2, conn_celltype))
                if norm_hist:
                    plt.savefig("%s/%s_%s_%s2%s_hist_norm.svg" % (self.filename, key, self.celltype1, self.celltype2, conn_celltype))
                else:
                    plt.savefig("%s/%s_%s_%s2%s_hist.svg" % (self.filename, key, self.celltype1, self.celltype2, conn_celltype))
            else:
                if title:
                    plt.title(title)
                else:
                    plt.title("%s from %s to %s, %s" % (key, conn_celltype, self.celltype1, self.celltype2))
                if norm_hist:
                    plt.savefig("%s/%s_%s2%s_%s_hist_norm.svg" % (self.filename, key, conn_celltype, self.celltype1, self.celltype2))
                else:
                    plt.savefig("%s/%s_%s2%s_%s_hist.svg" % (self.filename, key, conn_celltype, self.celltype1, self.celltype2))
        else:
            plt.title("%s in %s, %s" % (key, self.celltype1, self.celltype2))
            if norm_hist:
                plt.savefig("%s/%s_%s_%s_hist_norm.svg" % (self.filename, key, self.celltype1, self.celltype2))
            else:
                plt.savefig("%s/%s_%s_%s_hist.svg" % (self.filename, key, self.celltype1, self.celltype2))
        plt.close()


    def result_df_per_param(self, key, key2 = None, column_labels = None):
        """
        creates pd.Dataframe per parameter for easier plotting
        :param key: parameter to be compared as key in dictionary
        :param key2: if more than two groups
        :param column_labels: different column labels than celltypes when more than two groups
        :return: result_df
        """
        max_length = self.max_length_df
        if len(self.dictionary1[key]) > max_length:
            max_length = len(self.dictionary1[key])
        if len(self.dictionary2[key]) > max_length:
            max_length = len(self.dictionary2[key])
        if key2 is None:
            results_for_plotting = pd.DataFrame(columns=[self.celltype1, self.celltype2], index=range(max_length))
            results_for_plotting.loc[0:len(self.dictionary1[key]) - 1, self.celltype1] = self.dictionary1[key]
            results_for_plotting.loc[0:len(self.dictionary2[key]) - 1, self.celltype2] = self.dictionary2[key]
        else:
            try:
                key2_array = self.dictionary1[key2]
            except KeyError:
                key2_array = self.dictionary2[key2]
            key2_length = len(key2_array)
            if key2_length > self.max_length_df:
                max_length = key2_length
            if not column_labels:
                column_labels = [self.celltype1, self.celltype2, key2]
            results_for_plotting = pd.DataFrame(columns=column_labels, index=range(max_length))
            results_for_plotting.loc[0:len(self.dictionary1[key]) - 1, column_labels[0]] = self.dictionary1[key]
            results_for_plotting.loc[0:len(self.dictionary2[key]) - 1, column_labels[1]] = self.dictionary2[key]
            results_for_plotting.loc[0:key2_length - 1, column_labels[2]] = key2_array
        return results_for_plotting

    def result_df_categories(self, label_category):
        """
        creates da dataframe for comparison across keys and two parameters, one category will be a celltype comparison.
        keys should be organized in the way: column label - label e.g. number synapses - spine head
        :param: keys: list that includes one label
        :param label_category = in column_labels, category corresponding to labels
        :param key_split: if given, where key will be split into columns and labels
        :return: results_df
        """
        column_labels = []
        labels = []
        for ki, key in enumerate(self.dictionary1.keys()):
            if "-" in key:
                key_split = key.split(" - ")
                column_labels.append(key_split[0])
                labels.append(key_split[1])
        if len(column_labels) == 0:
            raise ValueError("keys in dictionary not labelled correctly")
        column_labels = np.hstack([np.unique(column_labels), ["celltype", label_category]])
        labels = np.unique(labels)
        key_example = column_labels[0] + " - " + labels[0]
        len_ct1 = len(self.dictionary1[key_example])
        len_ct2 = len(self.dictionary2[key_example])
        sum_length =  len_ct1 + len_ct2
        result_df = pd.DataFrame(
            columns=column_labels, index=range(sum_length * len(labels)))
        result_df[label_category] = type(labels[0])
        for i, label in enumerate(labels):
            result_df.loc[sum_length * i: sum_length * (i + 1) - 1, label_category] = label
            result_df.loc[sum_length * i: sum_length * i + len_ct1 - 1, "celltype"] = self.celltype1
            result_df.loc[sum_length * i + len_ct1: sum_length * (i + 1) - 1, "celltype"] = self.celltype2
            for ci in range(len(column_labels) - 2):
                result_df.loc[sum_length * i: sum_length * i + len_ct1 - 1, column_labels[ci]] = self.dictionary1[column_labels[ci] + " - " + label]
                result_df.loc[sum_length * i + len_ct1: sum_length * (i + 1) - 1, column_labels[ci]] = self.dictionary2[column_labels[ci] + " - " + label]
        for ci in range(len(column_labels) - 2):
            result_df[column_labels[ci]] = result_df[column_labels[ci]].astype("float64")
        return result_df

    def plot_violin(self, key, result_df, subcell, stripplot = True, conn_celltype = None, outgoing = False):
        """
        makes a violinplot of a specific parameter that is compared within two dictionaries.
        :param key: parameter that is compared
        :param result_df: dataframe containing results
        :param subcell: subcellular compartment
        :param stripplot: if true then stripplot will be overlayed
        :param conn_celltype: if connectivity to third celltype tested
        :param outgoing: if True, compared celltypes are presynaptic
        :return: None
        """
        sns.violinplot(data=result_df, inner="box", palette=self.color_palette)
        if stripplot:
            sns.stripplot(data=result_df, palette='dark:black', alpha=0.2, size = 2)
        plt.ylabel(self.param_label(key, subcell))
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if conn_celltype:
            if outgoing:
                plt.title("%s in %s, %s to%s" % (key, self.celltype1, self.celltype2, conn_celltype))
                plt.savefig(
                    "%s/%s_%s_%s_2_%s_violin.svg" % (self.filename, key, self.celltype1, self.celltype2, conn_celltype))
            else:
                plt.title("%s in %s to %s, %s" % (key, conn_celltype, self.celltype1, self.celltype2))
                plt.savefig("%s/%s_%s_2_%s_%s_violin.svg" % (self.filename, key, conn_celltype, self.celltype1, self.celltype2))
        else:
            plt.title("%s in %s, %s" % (key, self.celltype1, self.celltype2))
            plt.savefig("%s/%s_%s_%s_violin.svg" % (self.filename, key, self.celltype1, self.celltype2))
        plt.close()

    def plot_box(self, key, result_df, subcell, stripplot = True, conn_celltype = None, outgoing = False):
        """
        makes a violinplot of a specific parameter that is compared within two dictionaries.
        :param key: parameter that is compared
        :param result_df: dataframe containing results
        :param subcell: subcellular compartment
        :param stripplot: if true then stripplot will be overlayed
        :param conn_celltype: if connectivity to third celltype tested
        :param outgoing: if True, compared celltypes are presynaptic
        :return: None
        """
        sns.boxplot(data=result_df, palette=self.color_palette)
        if stripplot:
            sns.stripplot(data=result_df, palette='dark:black', alpha=0.2, size=2)
        plt.ylabel(self.param_label(key, subcell))
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if conn_celltype:
            if outgoing:
                plt.title("%s in %s, %s to%s" % (key, self.celltype1, self.celltype2, conn_celltype))
                plt.savefig(
                    "%s/%s_%s_%s_2_%s_box.svg" % (self.filename, key, self.celltype1, self.celltype2, conn_celltype))
            else:
                plt.title("%s in %s to %s, %s" % (key, conn_celltype, self.celltype1, self.celltype2))
                plt.savefig("%s/%s_%s_2_%s_%s_box.svg" % (self.filename, key, conn_celltype, self.celltype1, self.celltype2))
        else:
            plt.title("%s in %s, %s" % (key, self.celltype1, self.celltype2))
            plt.savefig("%s/%s_%s_%s_box.svg" % (self.filename, key, self.celltype1, self.celltype2))
        plt.close()

    def plot_violin_hue(self, key, x, hue, results_df, subcell, stripplot = True, conn_celltype = None, outgoing = False):
        """
        creates violin plot with more than one parameter. Dataframe with results oat least two parameter is required
        :param key: parameter to be plotted on y axis
        :param x: dataframe column on x axis
        :param hue: dataframe column acting as hue
        :param results_df: datafram, suitable one can be created with results_df_two_params
        :param stripplot: if True creates stripplot overlay
        :param conn_celltype: if third celltype connectivty is analysed
        :param outgoing: if true, connected_ct is post_synapse
        :return: None
        """
        if stripplot:
            sns.stripplot(x=x, y=key, data=results_df, hue=hue, palette='dark:black', alpha=0.2,
                          dodge=True, size = 2)
            ax = sns.violinplot(x=x, y=key, data=results_df.reset_index(), inner="box",
                                palette=self.color_palette, hue=hue)
            handles, labels = ax.get_legend_handles_labels()
            plt.legend(handles[0:2], labels[0:2])
            plt.ylabel(self.param_label(key, subcell))
        else:
            sns.violinplot(x = x, y= key, data = results_df, inner = "box", palette=self.color_palette, hue=hue)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if conn_celltype:
            if outgoing:
                plt.title('%s, %s/ %s to %s' % (key, self.celltype1, self.celltype2, conn_celltype))
                plt.savefig("%s/%s_%s_%s_2_%s_multi_violin.svg" % (
                    self.filename, key, self.celltype1, self.celltype2, conn_celltype))
            else:
                plt.title('%s, %s to %s/ %s' % (key, conn_celltype, self.celltype1, self.celltype2))
                plt.savefig("%s/%s_%s_2_%s_%s_multi_violin.svg" % (
                    self.filename, key, conn_celltype, self.celltype1, self.celltype2))
        else:
            plt.title('%s, between %s and %s in different compartments' % (key, self.celltype1, self.celltype2))
            plt.savefig("%s/%s_%s_%s_multi_violin.svg" % (self.filename, key, self.celltype1, self.celltype2))
        plt.close()

    def plot_box_hue(self, key, x, hue, results_df, subcell, stripplot = True, conn_celltype = None, outgoing = False):
        """
        creates box plot with more than one parameter. Dataframe with results oat least two parameter is required
        :param key: parameter to be plotted on y axis
        :param x: dataframe column on x axis
        :param hue: dataframe column acting as hue
        :param results_df: datafram, suitable one can be created with results_df_two_params
        :param stripplot: if True creates stripplot overlay
        :param conn_celltype: if third celltype connectivty is analysed
        :param outgoing: if true, connected_ct is post_synapse
        :return: None
        """
        if stripplot:
            sns.stripplot(x=x, y=key, data=results_df, hue=hue, palette='dark:black', alpha=0.2,
                          dodge=True, size = 2)
            ax = sns.boxplot(x=x, y=key, data=results_df.reset_index(),
                                palette=self.color_palette, hue=hue)
            handles, labels = ax.get_legend_handles_labels()
            plt.legend(handles[0:2], labels[0:2])
            plt.ylabel(self.param_label(key, subcell))
        else:
            sns.boxplot(x=x, y=key, data=results_df, palette=self.color_palette, hue=hue)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if conn_celltype:
            if outgoing:
                plt.title('%s, %s/ %s to %s' % (key, self.celltype1, self.celltype2, conn_celltype))
                plt.savefig("%s/%s_%s_%s_2_%s_multi_box.svg" % (
                    self.filename, key, self.celltype1, self.celltype2, conn_celltype))
            else:
                plt.title('%s, %s to %s/ %s' % (key, conn_celltype, self.celltype1, self.celltype2))
                plt.savefig("%s/%s_%s_2_%s_%s_multi_box.svg" % (
                    self.filename, key, conn_celltype, self.celltype1, self.celltype2))
        else:
            plt.title('%s, between %s and %s in different compartments' % (key, self.celltype1, self.celltype2))
            plt.savefig("%s/%s_%s_%s_multi_box.svg" % (self.filename, key, self.celltype1, self.celltype2))
        plt.close()

    def plot_bar_hue(self, key, x, hue, results_df, conn_celltype=None, outgoing=False):
        """
        creates box plot with more than one parameter. Dataframe with results oat least two parameter is required
        :param key: parameter to be plotted on y axis
        :param x: dataframe column on x axis
        :param hue: dataframe column acting as hue
        :param results_df: datafram, suitable one can be created with results_df_two_params
        :param stripplot: if True creates stripplot overlay
        :param conn_celltype: if third celltype connectivty is analysed
        :param outgoing: if true, connected_ct is post_synapse
        :return: None
        """
        sns.barplot(x=x, y=key, data=results_df, palette=self.color_palette, hue=hue, orient="h")
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if conn_celltype:
            if outgoing:
                plt.title('%s, %s/ %s to %s' % (key, self.celltype1, self.celltype2, conn_celltype))
                plt.savefig("%s/%s_%s_%s_%s_2_%s_multi_bar.svg" % (
                    self.filename, key, x, self.celltype1, self.celltype2, conn_celltype))
            else:
                plt.title('%s, %s to %s/ %s' % (key, conn_celltype, self.celltype1, self.celltype2))
                plt.savefig("%s/%s_%s_%s_2_%s_%s_multi_bar.svg" % (
                    self.filename, key, x, conn_celltype, self.celltype1, self.celltype2))
        else:
            plt.title('%s, between %s and %s in different compartments' % (key, self.celltype1, self.celltype2))
            plt.savefig("%s/%s_%s_%s_%s_multi_bar.svg" % (self.filename, key,x, self.celltype1, self.celltype2))
        plt.close()


class ComparingMultipleForPLotting(ResultsForPlotting):
    """
    makes plots from multiple dictionaries with the same keys to compare their results.If only two dictionaries better use ComparingResultsForPlotting.
    """
    def __init__(self, ct_list, filename, dictionary_list, colour_list):
        super().__init__(ct_list[0], filename, dictionary_list[0])
        if len(ct_list) < 2:
            raise ValueError("this class needs at least two celltypes")
        self.number_celltypes = len(ct_list)
        self.celltypes = {i: ct_list[i] for i in range(self.number_celltypes)}
        self.celltype_labels = ct_list
        self.dictionaries = {i: dictionary_list[i] for i in range(self.number_celltypes)}
        self.color_palette= {ct_list[i]: colour_list[i] for i in range(self.number_celltypes)}

    def plot_box(self, key, result_df, subcell, x=None, stripplot = True, outgoing = False):
        """
        makes a violinplot of a specific parameter that is compared within two dictionaries.
        :param key: parameter that is compared
        :param result_df: dataframe containing results
        :param subcell: subcellular compartment
        :param stripplot: if true then stripplot will be overlayed
        :return: None
        """
        if x is None:
            sns.boxplot(data=result_df, palette=self.color_palette)
            if stripplot:
                sns.stripplot(data=result_df, palette='dark:black', alpha=0.2, size = 2)
        else:
            sns.boxplot(x = x, y = key, data=result_df, palette=self.color_palette)
            if stripplot:
                sns.stripplot(x = x, y = key, data=result_df, palette='dark:black', alpha=0.2, size = 2)
        plt.ylabel(self.param_label(key, subcell))
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if outgoing:
            plt.title("%s from %s, %s, %s" % (key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
            plt.savefig(
                "%s/%s_%s_%s_%s_box_outgoing.svg" % (
                    self.filename, key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
        else:
            plt.title("%s in %s, %s, %s" % (key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
            plt.savefig(
                "%s/%s_%s_%s_%s_box.svg" % (
                self.filename, key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
        plt.close()

    def plot_violin(self, key, result_df, subcell , x=None, stripplot = True, outgoing = False):
        """
        makes a violinplot of a specific parameter that is compared within two dictionaries.
        :param key: parameter that is compared
        :param result_df: dataframe containing results
        :param subcell: subcellular compartment
        :param stripplot: if true then stripplot will be overlayed
        :return: None
        """
        if x is None:
            sns.violinplot(data=result_df, inner="box", palette=self.color_palette)
            if stripplot:
                sns.stripplot(data=result_df, color='black', alpha=0.2, size = 2)
        else:
            sns.violinplot(x = x, y = key,data=result_df, inner="box", palette=self.color_palette)
            if stripplot:
                sns.stripplot(x = x, y = key, data=result_df, color='black', alpha=0.2, size = 2)
        plt.ylabel(self.param_label(key, subcell))
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if outgoing:
            plt.title("%s from %s, %s, %s" % (key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
            plt.savefig(
                "%s/%s_%s_%s_%s_violin_outgoing.svg" % (
                self.filename, key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
        else:
            plt.title("%s in %s, %s, %s" % (key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
            plt.savefig(
                "%s/%s_%s_%s_%s_violin.svg" % (self.filename, key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
        plt.close()

    def plot_hist_comparison(self, key, subcell, result_df, hue = None, cells = True, norm_hist = False, bins = None, xlabel = None, outgoing = False):
        """
                 plots two arrays and compares them in histogram and saves it.
                 :param key: key of dictionary that should be plotted
                 :param subcell: compartment or subcellular structure that will be plotted
                 :param cells: True: cells are plotted, False: subcellular structures are plotted
                 :param norm_hist: if true: histogram will be normed
                 :param bins: number of bins
                 :param xlabel: label of x axis, not needed if clear from key
                 :return: None
                 """
        if bins is None:
            bins = "auto"
        if norm_hist:
            if hue is None:
                sns.histplot(result_df, fill=False, element="step", bins=bins, common_norm=True, legend=True,
                             palette=self.color_palette, linewidth=3)
            else:
                sns.histplot(result_df, x= key, hue = hue, fill=False, element="step", bins=bins, common_norm=True, legend=True,
                             palette=self.color_palette, linewidth=3)
            if cells:
                plt.ylabel("fraction of cells")
            elif "pair" in key:
                plt.ylabel("fraction of %s pairs" % subcell)
            else:
                plt.ylabel("fraction of %s" % subcell)
        else:
            if hue is None:
                sns.histplot(result_df, fill=False, element="step", bins=bins, common_norm=False, legend=True,
                         palette=self.color_palette, linewidth=3)
            else:
                sns.histplot(result_df, x=key, hue=hue, fill=False, element="step", bins=bins, common_norm=True,
                             legend=True,
                             palette=self.color_palette, linewidth=3)
            if cells:
                plt.ylabel("count of cells")
            elif "pair" in key:
                plt.ylabel("count of %s pairs" % subcell)
            else:
                plt.ylabel("count of %s" % subcell)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if xlabel:
            plt.xlabel(xlabel)
        else:
            plt.xlabel(self.param_label(key, subcell))
        if outgoing:
            plt.title("%s from %s, %s, %s" % (key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
            if norm_hist:
                plt.savefig("%s/%s_%s_%s_%s_hist_norm_outgoing.svg" % (self.filename, key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
            else:
                plt.savefig("%s/%s_%s_%s_%s_hist_outgoing.svg" % (self.filename, key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
        else:
            plt.title("%s in %s, %s, %s" % (key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
            if norm_hist:
                plt.savefig("%s/%s_%s_%s_%s_hist_norm.svg" % (self.filename, key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
            else:
                plt.savefig("%s/%s_%s_%s_%s_hist.svg" % (self.filename, key, self.celltypes[0], self.celltypes[1], self.celltypes[2]))
        plt.close()

    def result_df_categories(self, label_category):
        """
        creates da dataframe for comparison across keys and two parameters, one category will be a celltype comparison.
        keys should be organized in the way: column label - label e.g. number synapses - spine head
        :param: keys: list that includes one label
        :param label_category = in column_labels, category corresponding to labels
        :param key_split: if given, where key will be split into columns and labels
        :return: results_df
        """
        column_labels = []
        labels = []
        for ki, key in enumerate(self.dictionaries[0].keys()):
            if "-" in key:
                key_split = key.split(" - ")
                column_labels.append(key_split[0])
                labels.append(key_split[1])
        if len(column_labels) == 0:
            raise ValueError("keys in dictionary not labelled correctly")
        celltypes = [self.celltypes[i] for i in range(self.number_celltypes)]
        columns = np.hstack([np.unique(column_labels), "celltype", label_category])
        labels = np.unique(labels)
        key_example = column_labels[0] + " - " + labels[0]
        dict_lengths = np.array([len(self.dictionaries[i][key_example]) for i in range(self.number_celltypes)])
        sum_length = np.sum(dict_lengths)
        result_df = pd.DataFrame(
            columns=columns, index=range(sum_length * len(labels)))
        result_df[label_category] = type(labels[0])
        for i, label in enumerate(labels):
            result_df.loc[sum_length * i: sum_length * (i + 1) - 1, label_category] = label
            start_length_ct = 0
            for j in range(self.number_celltypes):
                end_length_ct = dict_lengths[j] + start_length_ct
                result_df.loc[sum_length * i + start_length_ct: sum_length * i + end_length_ct -1 , "celltype"] = self.celltypes[j]
                for ci in range(len(column_labels) - 2):
                    result_df.loc[sum_length * i + start_length_ct: sum_length * i + end_length_ct - 1, column_labels[ci]] = self.dictionaries[j][column_labels[ci] + " - " + label]
                start_length_ct += dict_lengths[j]
        for ci in range(len(column_labels) - 2):
            result_df[column_labels[ci]] = result_df[column_labels[ci]].astype("float64")
        return result_df

    def result_df_per_param(self, key):
        """
        creates pd.Dataframe per parameter for easier plotting
        :param key: parameter to be compared as key in dictionary
        :param key2: if more than two groups
        :param column_labels: different column labels than celltypes when more than two groups
        :return: result_df
        """
        dict_lengths = np.array([len(self.dictionaries[i][key]) for i in range(self.number_celltypes)])
        max_length = np.max(dict_lengths)
        results_for_plotting = pd.DataFrame(columns=self.celltype_labels, index=range(max_length))
        for i in range(self.number_celltypes):
            results_for_plotting.loc[0:len(self.dictionaries[i][key]) - 1, self.celltypes[i]] = self.dictionaries[i][key]
        return results_for_plotting

    def plot_violin_hue(self, key, x, hue, results_df, subcell, stripplot = True, conn_celltype = None, outgoing = False):
        """
        creates violin plot with more than one parameter. Dataframe with results oat least two parameter is required
        :param key: parameter to be plotted on y axis
        :param x: dataframe column on x axis
        :param hue: dataframe column acting as hue
        :param results_df: datafram, suitable one can be created with results_df_two_params
        :param stripplot: if True creates stripplot overlay
        :param conn_celltype: if third celltype connectivty is analysed
        :param outgoing: if true, connected_ct is post_synapse
        :return: None
        """
        if stripplot:
            sns.stripplot(x=x, y=key, data=results_df, hue=hue, palette='dark:black', alpha=0.2,
                          dodge=True, size=2)
            ax = sns.violinplot(x=x, y=key, data=results_df.reset_index(), inner="box",
                                palette=self.color_palette, hue=hue)
            handles, labels = ax.get_legend_handles_labels()
            plt.legend(handles[0:2], labels[0:2])
            plt.ylabel(self.param_label(key, subcell))
        else:
            sns.violinplot(x = x, y= key, data = results_df, inner = "box", palette=self.color_palette, hue=hue)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if conn_celltype:
            if outgoing:
                plt.title('%s, %s/ %s to %s' % (key, self.celltypes[0], self.celltypes[1], conn_celltype))
                plt.savefig("%s/%s_%s_%s_2_%s_multi_violin.svg" % (
                    self.filename, key, self.celltypes[0], self.celltypes[1], conn_celltype))
            else:
                plt.title('%s, %s to %s/ %s' % (key, conn_celltype, self.celltypes[0], self.celltypes[1]))
                plt.savefig("%s/%s_%s_2_%s_%s_multi_violin.svg" % (
                    self.filename, key, conn_celltype, self.celltypes[0], self.celltypes[1]))
        else:
            plt.title('%s, between %s and %s in different compartments' % (key, self.celltypes[0], self.celltypes[1]))
            plt.savefig("%s/%s_%s_%s_multi_violin.svg" % (self.filename, key, self.celltypes[0], self.celltypes[1]))
        plt.close()

    def plot_box_hue(self, key, x, hue, results_df, subcell, stripplot = True, conn_celltype = None, outgoing = False):
        """
        creates box plot with more than one parameter. Dataframe with results oat least two parameter is required
        :param key: parameter to be plotted on y axis
        :param x: dataframe column on x axis
        :param hue: dataframe column acting as hue
        :param results_df: datafram, suitable one can be created with results_df_two_params
        :param stripplot: if True creates stripplot overlay
        :param conn_celltype: if third celltype connectivty is analysed
        :param outgoing: if true, connected_ct is post_synapse
        :return: None
        """
        if stripplot:
            sns.stripplot(x=x, y=key, data=results_df, hue=hue, palette='dark:black', alpha=0.2,
                          dodge=True, s = 2)
            ax = sns.boxplot(x=x, y=key, data=results_df.reset_index(),
                                palette=self.color_palette, hue=hue)
            handles, labels = ax.get_legend_handles_labels()
            plt.legend(handles[0:2], labels[0:2])
            plt.ylabel(self.param_label(key, subcell))
        else:
            sns.boxplot(x=x, y=key, data=results_df, palette=self.color_palette, hue=hue)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if conn_celltype:
            if outgoing:
                plt.title('%s, %s/ %s to %s' % (key, self.celltypes[0], self.celltypes[1], conn_celltype))
                plt.savefig("%s/%s_%s_%s_2_%s_multi_box.svg" % (
                    self.filename, key, self.celltypes[0], self.celltypes[1], conn_celltype))
            else:
                plt.title('%s, %s to %s/ %s' % (key, conn_celltype,self.celltypes[0], self.celltypes[1]))
                plt.savefig("%s/%s_%s_2_%s_%s_multi_box.svg" % (
                    self.filename, key, conn_celltype, self.celltypes[0], self.celltypes[1]))
        else:
            plt.title('%s, between %s and %s in different compartments' % (key, self.celltypes[0], self.celltypes[1]))
            plt.savefig("%s/%s_%s_%s_multi_box.svg" % (self.filename, key, self.celltypes[0], self.celltypes[1]))
        plt.close()

    def plot_bar_hue(self, key, x, hue, results_df, conn_celltype=None, outgoing=False):
        """
        creates box plot with more than one parameter. Dataframe with results oat least two parameter is required
        :param key: parameter to be plotted on y axis
        :param x: dataframe column on x axis
        :param hue: dataframe column acting as hue
        :param results_df: datafram, suitable one can be created with results_df_two_params
        :param stripplot: if True creates stripplot overlay
        :param conn_celltype: if third celltype connectivty is analysed
        :param outgoing: if true, connected_ct is post_synapse
        :return: None
        """
        sns.barplot(x=x, y=key, data=results_df, palette=self.color_palette, hue=hue, orient="h")
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        if conn_celltype:
            if outgoing:
                plt.title('%s, %s/ %s to %s' % (key, self.celltypes[0], self.celltypes[1], conn_celltype))
                plt.savefig("%s/%s_%s_%s_%s_2_%s_multi_bar.svg" % (
                    self.filename, key, x, self.celltypes[0], self.celltypes[1], conn_celltype))
            else:
                plt.title('%s, %s to %s/ %s' % (key, conn_celltype, self.celltypes[0], self.celltypes[1]))
                plt.savefig("%s/%s_%s_%s_2_%s_%s_multi_bar.svg" % (
                    self.filename, key, x, conn_celltype, self.celltypes[0], self.celltypes[1]))
        else:
            plt.title('%s, between %s and %s in different compartments' % (key, self.celltypes[0], self.celltypes[1]))
            plt.savefig("%s/%s_%s_%s_%s_multi_bar.svg" % (self.filename, key,x, self.celltypes[0], self.celltypes[1]))
        plt.close()


class ConnMatrix():
    '''
    This class can be used for plotting connectivty matrixes. Presynaptic partners are on the y, postsynaptic partners on the x-axis.
    '''
    def __init__(self, data, title, filename, cmap = sns.color_palette('flare', as_cmap=True)):
        self.data = data
        self.title = title
        self.cmap = cmap
        self.filename = filename

    def get_heatmap(self, save_svg = False, annot = False, fontsize = 10, center_zero = False):
        if center_zero:
            sns.heatmap(self.data, cbar=True, cmap=self.cmap, annot=annot, fmt='.1f', center= 0.0)
        else:
            sns.heatmap(self.data, cbar=True, cmap=self.cmap, annot = annot, fmt='.1f')
        plt.xlabel('Postsynaptic partners')
        plt.ylabel('Presynaptic partners')
        plt.title(self.title)
        plt.xticks(fontsize=fontsize)
        plt.yticks(fontsize=fontsize)
        plt.savefig('%s/%s.png' % (self.filename, self.title))
        if save_svg:
            plt.savefig('%s/%s.svg' % (self.filename, self.title))
        plt.close()


def plot_nx_graph(results_dictionary, filename, title):
    G = nx.DiGraph()
    edges = [[u, v, results_dictionary[(u, v)]] for (u, v) in results_dictionary.keys()]
    G.add_weighted_edges_from(edges)
    weights = [G[u][v]["weight"] / 200 for (u, v) in G.edges()]
    labels = nx.get_edge_attributes(G, "weight")
    labels = {key: int(labels[key]) for key in labels}
    pos = nx.spring_layout(G, seed=7)
    fig = plt.figure(figsize=(15, 15))
    nx.draw_networkx_nodes(G, pos, node_size=3000)
    nx.draw_networkx_labels(G, pos, font_size=16)
    nx.draw_networkx_edges(G, pos, width=weights, arrows=True, connectionstyle="arc3, rad=0.3", arrowstyle= matplotlib.patches.ArrowStyle.Fancy(head_length=3.4, head_width=1.6))
    #nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, label_pos=0.2)
    ax = plt.gca()
    ax.margins(0.08)
    plt.axis("off")
    plt.tight_layout()
    plt.title(title)
    plt.savefig(filename)
    plt.close()

def plot_histogram_selection(dataframe, x_data, color_palette, label, count, foldername, hue_data = None, title = None, fontsize = None):
    '''
    Function to plot multiple histograms of the same data, preferebly with two or more groups
    to compare.
    :param dataframe: pandas dataframe with data to be plottet
    :param x_data: column name for data to plot on x-axis
    :param color_palette: color palette to use
    :param label: additional information for title and saving
    :param count: label of entities counted e.g. 'cells', 'synapses'
    :param foldername: name of folder where plots are supposed to be stored
    :param hue_data: if comparing several groups, name of column
    :param title: if given used as plot title, otherwise x_dtaa and count used
    :return: None
    '''

    if 'area' in x_data or 'size' in x_data:
        xlabel = f'{x_data} [µm²]'
    else:
        xlabel = x_data

    if title is None:
        plottitle = f'{x_data} for {count}'
    else:
        plottitle = title

    sns.histplot(x=x_data, data=dataframe, hue=hue_data, palette=color_palette, common_norm=False,
                 fill=False, element="step", linewidth=3, legend=True)
    plt.ylabel(f'number of {count}', fontsize = fontsize)
    plt.xlabel(xlabel, fontsize = fontsize)
    plt.xticks(fontsize = fontsize)
    plt.yticks(fontsize = fontsize)
    plt.title(plottitle)
    plt.savefig(f'{foldername}/{label}_hist.png')
    plt.savefig(f'{foldername}/{label}_hist.svg')
    plt.close()
    sns.histplot(x=x_data, data=dataframe, hue=hue_data, palette=color_palette, common_norm=False,
                 fill=False, element="step", linewidth=3, legend=True, stat='percent')
    plt.ylabel(f'% of {count}', fontsize = fontsize)
    plt.xlabel(xlabel, fontsize = fontsize)
    plt.xticks(fontsize=fontsize)
    plt.yticks(fontsize=fontsize)
    plt.title(plottitle)
    plt.savefig(f'{foldername}/{label}_hist_perc.png')
    plt.savefig(f'{foldername}/{label}_hist_perc.svg')
    plt.close()
    sns.histplot(x=x_data, data=dataframe, hue=hue_data, palette=color_palette, common_norm=False,
                 fill=False, element="step", linewidth=3, legend=True, log_scale=True)
    plt.ylabel(f'number of {count}', fontsize = fontsize)
    plt.xlabel(xlabel, fontsize = fontsize)
    plt.xticks(fontsize=fontsize)
    plt.yticks(fontsize=fontsize)
    plt.title(plottitle)
    plt.savefig(f'{foldername}/{label}_hist_log.png')
    plt.savefig(f'{foldername}/{label}_hist_log.svg')
    plt.close()
    sns.histplot(x=x_data, data=dataframe, hue=hue_data, palette=color_palette, common_norm=False,
                 fill=False, element="step", linewidth=3, legend=True, stat='percent', log_scale=True)
    plt.ylabel(f'% of {count}', fontsize = fontsize)
    plt.xlabel(xlabel, fontsize = fontsize)
    plt.xticks(fontsize=fontsize)
    plt.yticks(fontsize=fontsize)
    plt.title(plottitle)
    plt.savefig(f'{foldername}/{label}_hist_log_perc.png')
    plt.savefig(f'{foldername}/{label}_hist_log_perc.svg')
    plt.close()



