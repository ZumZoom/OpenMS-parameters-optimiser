import xml.dom.minidom
import re
from configuration_optimiser import ConfigurationOptimiser
from id_mapper_optimiser import IDMapperOptimiser
from constants import *

__author__ = 'zumzoom'


class FeatureFinderOptimiser(ConfigurationOptimiser):
    def __init__(self, config):
        ConfigurationOptimiser.__init__(self, config)
        self.optimisation_elements = [('mz_tolerance', 0), ('min_spectra', 0), ('max_missing', 0),
                                      ('slope_bound', 0),
                                      ('charge_low', 0), ('charge_high', 0), ('mz_tolerance', 1),
                                      ('intensity_percentage', 0), ('intensity_percentage_optional', 0),
                                      ('optional_fit_improvement', 0), ('mass_window_width', 0),
                                      ('abundance_12C', 0), ('abundance_14N', 0),
                                      ('min_score', 0), ('epsilon_abs', 0), ('epsilon_rel', 0),
                                      ('min_score', 1), ('min_isotope_fit', 0), ('min_trace_score', 0),
                                      ('min_rt_span', 0), ('max_rt_span', 0), ('max_intersection', 0)]
        self.working_ini_file = WORKING_INI_FFC_FILE
        self.ini_to_save = SAVED_INI_FFC_FILE
        self.dom = xml.dom.minidom.parse(SAVED_INI_FFC_FILE)

    def get_args(self, i=0):
        return self.config.ffc, '-in', self.config.mzml[i], '-out', str(i)+'_'+DEFAULT_FFC_OUTPUT_FILE, \
               '-ini', WORKING_INI_FFC_FILE

    def get_result(self, output, i):
        m = re.search(r"FeatureFinderCentroided took (\d*\.?\d*) s \(wall\)", output)
        if m:
            t = float(m.group(1))
        else:
            m = re.search(r"FeatureFinderCentroided took (\d\d):(\d\d) m \(wall\)", output)
            if m:
                t = float(m.group(1)) * 60 + float(m.group(2))
            else:
                raise Exception("No result")
        opt = IDMapperOptimiser(self.config)
        opt.write_config(opt.working_ini_file)
        args = opt.get_args(i)
        output = opt.run_program(args, False)
        return {'value': opt.get_result(output, i), 'time': t}
        # return opt.get_result(output)

    def cmp_result(self, res, best):
        return res['value'] > best['value'] or (res['value'] == best['value'] and res['time'] + 3 < best['time'])

    def low_result(self, res, best):
        return res['value'] < 0.99 * best['value']

    def pre_loading(self):
        pass

    def add_res(self, res1, res2):
        return {'value': res1['value'] + res2['value'], 'time': res1['time'] + res2['time']}