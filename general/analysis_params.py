#this file sets general analysis values
from syconn.handler.basics import load_pkl2obj
import numpy as np

class Analysis_Params(object):
    '''
    Config object for setting general analysis parameters
    TO DO: base on file
    '''
    def __init__(self, version):
        self._version = version
        ct_dict = {'v3': {}, 'v4': {0: "STN", 1: "DA", 2: "MSN", 3: "LMAN", 4: "HVC", 5: "TAN", 6: "GPe", 7: "GPi", 8: "FS", 9: "LTS",
               10: "NGF"}, 'v5': {0: "STN", 1: "DA", 2: "MSN", 3: "LMAN", 4: "HVC", 5: "TAN", 6: "GPe", 7: "GPi", 8: "FS", 9: "LTS",
               10: "NGF", 11:"ASTRO", 12:"OLIGO", 13:'MICRO', 14:'FRAG'},
                   'v6': {0:'DA', 1:'LMAN', 2: 'HVC', 3:'MSN', 4:'STN', 5:'TAN', 6:'GPe', 7:'GPi', 8: 'LTS',
                          9:'INT1', 10:'INT2', 11:'INT3', 12:'ASTRO', 13:'OLIGO', 14:'MICRO', 15:'MIGR', 16:'FRAG'}}
        working_dir_dict = {'v4':'/cajal/nvmescratch/projects/from_ssdscratch/songbird/j0251/j0251_72_seg_20210127_agglo2',
                       'v5':'/cajal/nvmescratch/projects/data/songbird_tmp/j0251/j0251_72_seg_20210127_agglo2_syn_20220811',
                       'v6':'/cajal/nvmescratch/projects/data/songbird/j0251/j0251_72_seg_20210127_agglo2_syn_20220811_celltypes_20230822'}
        self._working_dir = working_dir_dict[version]
        self._ct_dict = ct_dict[version]
        if version == 'v4':
            self._axon_cts = [1, 3, 4]
        if version == 'v5':
            self._glia_cts = [11, 12, 13, 14]
            self._axon_cts = [1, 3, 4]
        elif version == 'v6':
            self._glia_cts = [12, 13, 14, 15, 16]
            self._axon_cts = [0, 1, 2]
        else:
            self._glia_cts = []
        self._num_cts = len(self._ct_dict.keys())
        self._axoness_dict = {0: 'dendrite', 1:'axon', 2:'soma'}
        self._spiness_dict = {0: 'spine neck', 1: 'spine head', 2:'dendritic shaft', 3:'other'}
        self._syn_prob_tresh = 0.6
        self._min_syn_size = 0.1
        self._min_comp_length = 200
        self.file_locations = f"/cajal/nvmescratch/users/arother/j0251{self._version}_prep/"
        self._merger_file_location = f'{self.file_locations}/merger_arr.pkl'
        self._pot_astros_file_location = f'{self.file_locations}/pot_astro_ids.pkl'
        celltype_keys = {'v3':'celltype_cnn_e3', 'v4':'celltype_cnn_e3', 'v5':'celltype_pts_e3', 'v6':'celltype_pts_e3'}
        celltype_keys_certainty = {'v3': 'celltype_cnn_e3_certainty', 'v4': 'celltype_cnn_e3_certainty', 'v5': 'celltype_pts_e3_certainty',
                         'v6': 'celltype_pts_e3_certainty'}
        self._celltype_key = celltype_keys[version]
        self._celltype_certainty_key = celltype_keys_certainty[version]

    def working_dir(self):
        return self._working_dir

    def ct_dict(self, with_glia = False):
        if with_glia:
            return self._ct_dict
        else:
            ct_dict = {i: self._ct_dict[i] for i in range(self._num_cts) if i not in self._glia_cts}
            return ct_dict

    def ct_str(self, with_glia = False):
        #return celltype names as list of str
        if with_glia:
            ct_str = [self._ct_dict[i] for i in range(self._num_cts)]
        else:
            ct_str = [self._ct_dict[i] for i in range(self._num_cts) if i not in self._glia_cts]
        return ct_str

    def num_cts(self, with_glia = False):
        if with_glia:
            return self._num_cts
        else:
            return self._num_cts - len(self._glia_cts)

    def axoness_dict(self):
        return self.axoness_dict

    def axon_cts(self):
        return self._axon_cts

    def glia_cts(self):
        return self._glia_cts

    def syn_prob_thresh(self):
        return self._syn_prob_tresh

    def min_syn_size(self):
        return self._min_syn_size

    def min_comp_length(self):
        return self._min_comp_length

    def load_known_mergers(self):
        mergers = load_pkl2obj(self._merger_file_location)
        return mergers

    def load_potential_astros(self):
        potential_astrocytes = load_pkl2obj(self._pot_astros_file_location)
        return potential_astrocytes

    def celltype_key(self):
        return self._celltype_key

    def celltype_certainty_key(self):
        return self._celltype_certainty_key

    def load_cell_dict(self, celltype):
        if self._version == 'v6':
            if celltype in self._axon_cts:
                cell_dict = load_pkl2obj(f'{self.file_locations}/ax_{self._ct_dict[celltype]}_dict.pkl')
            else:
                cell_dict = load_pkl2obj(f'{self.file_locations}/full_{self._ct_dict[celltype]}_dict.pkl')
        else:
            if celltype in self._axon_cts:
                cell_dict = load_pkl2obj(f'{self.file_locations}/ax_{self._ct_dict[celltype]:.3s}_dict.pkl')
            else:
                cell_dict = load_pkl2obj(f'{self.file_locations}/full_{self._ct_dict[celltype]:.3s}_dict.pkl')
        return cell_dict

    def load_full_cell_array(self, celltype):
        if celltype in self._axon_cts:
            raise ValueError('This function is only available for full cells. You are trying to load it with a celltype where only axons are available')
        else:
            if self._version == 'v6':
                cell_array = load_pkl2obj(f'{self.file_locations}/full_{self._ct_dict[celltype]:}_arr.pkl')
            else:
                cell_array = load_pkl2obj(f'{self.file_locations}/full_{self._ct_dict[celltype]:.3s}_arr.pkl')
        return cell_array

    def celltype_key(self):
        return self._celltype_key

    def load_celltypes_full_cells(self, with_glia = False):
        ct_types = np.arange(self.num_cts(with_glia=with_glia))
        full_ct_types = ct_types[np.in1d(ct_types, self._axon_cts) == False]
        return full_ct_types

    def load_ngf_subids(self, type):
        #either type 1 or type 2
        ids = load_pkl2obj(f'{self.file_locations}/ngf_type{type}_ids.pkl')
        return ids

    def load_msn_subids(self, type, min_comp_len = 200):
        msn_sub_dict = {'MSN only GPi':'2_GPi', 'MSN only GPe':'2_GPe', 'MSN both GP':'2_GPeGPi', 'MSN no GP':'no_conn_GPeGPi'}
        try:
            ids = load_pkl2obj(f'{self.file_locations}/full_MSN_{msn_sub_dict[type]}_arr_{min_comp_len}.pkl')
        except FileNotFoundError:
            raise FileNotFoundError('no msn subgroup ids for either this type or this compartment length saved')
        return ids

    def load_handpicked_ids(self, celltype, ct_dict = None):
        'Loads celltypes but only if file name has handpicked in it'
        if ct_dict is None:
            ct_dict = self._ct_dict
        try:
            cell_array = load_pkl2obj(f'{self.file_locations}/handpicked_{ct_dict[celltype]:}_ids.pkl')
        except FileNotFoundError:
            try:
                cell_array = np.load(f'{self.file_locations}/handpicked_{ct_dict[celltype]:}_ids.npy')
            except FileNotFoundError:
                raise FileNotFoundError('no handpicked cells exist for this celltype')
        return cell_array



        