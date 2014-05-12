import xml.dom.minidom
from configuration_optimiser import ConfigurationOptimiser
from features_extractor import get_data_to_delete
from constants import *

__author__ = 'zumzoom'


class IDMapperOptimiser(ConfigurationOptimiser):
    def __init__(self, config):
        ConfigurationOptimiser.__init__(self, config)
        self.optimisation_elements = [('rt_tolerance', 0), ('mz_tolerance', 0)]
        self.working_ini_file = WORKING_INI_IDM_FILE
        self.ini_to_save = SAVED_INI_IDM_FILE
        self.dom = xml.dom.minidom.parse(SAVED_INI_IDM_FILE)

    def get_args(self, i=0):
        return (self.config.idm, '-in', str(i)+'_'+DEFAULT_FFC_OUTPUT_FILE, '-out', DEFAULT_IDM_OUTPUT_FILE, '-id',
                self.config.idxml, '-ini', WORKING_INI_IDM_FILE)

    def get_result(self, output, i):
        features, peptides = get_data_to_delete(str(i)+'_'+DEFAULT_FFC_OUTPUT_FILE)
        return len(peptides)

    def cmp_result(self, res, best):
        return res > best

    def low_result(self, res, best):
        return res < 0.99 * best

    def pre_loading(self):
        for i in range(len(self.config.mzml)):
            args = (self.config.ffc, '-in', self.config.mzml[i], '-out', str(i)+'_'+DEFAULT_FFC_OUTPUT_FILE,
                    '-ini', SAVED_INI_FFC_FILE)
            self.run_program(args, False)

    def add_res(self, res1, res2):
        return res1 + res2