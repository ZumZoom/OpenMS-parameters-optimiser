__author__ = 'zumzoom'

import xml.dom.minidom
import argparse
import re
from subprocess import Popen, PIPE
import abc
import logging

# int_regex = re.compile(r"^(\d*\.?\d*):(\d*\.?\d*)$")
# string_regex = re.compile(r"^(\w,)*\w*$")

DEFAULT_PRINT_ATTRIBUTES = ['name', 'value', 'type', 'restrictions', 'required', 'advanced']
DEFAULT_SKIPPED_ELEMENTS = ['version', 'in', 'out', 'seeds', 'log', 'debug', 'threads', 'no_progress', 'test', 'debug']
DEFAULT_FFC_OUTPUT_FILE = 'full_noise0.featureXML'
DEFAULT_IDM_OUTPUT_FILE = 'out_IDM.featureXML'
WORKING_INI_FFC_FILE = 'feature_finder_custom.ini'
WORKING_INI_IDM_FILE = 'id_mapper_custom.ini'


class Singleton:
    def __init__(self, decorated):
        self._decorated = decorated
        self._instance = None

    def instance(self):
        if self._instance is not None:
            return self._instance
        else:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


@Singleton
class Logger():
    def __init__(self):
        self.logger = logging.getLogger('logger')
        handler = logging.FileHandler('log.txt')
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log(self, what):
        self.logger.info(what)


def log(what):
    Logger.instance().log(what)


class ConfigurationOptimiser():
    __metaclass = abc.ABCMeta
    optimisation_elements = []

    def __init__(self, config):
        self.dom = None
        self.config = config
        self.optimisation_elements = []
        self.working_ini_file = None
        self.lower_bound = None
        self.upper_bound = None

    def get_element(self, name, offset):
        for elem in self.dom.getElementsByTagName('ITEM'):
            if elem.getAttribute('name') == name:
                if offset > 0:
                    offset -= 1
                    continue
                return elem

    @staticmethod
    def parse_restrictions(elem):
        elem_type = elem.getAttribute('type')
        restrictions = []
        if elem_type == 'string':
            restrictions = re.split(',', elem.getAttribute('restrictions'))
        elif elem_type == 'int' or elem_type == 'double':
            restrictions = re.split(':', elem.getAttribute('restrictions'))
        elif elem_type == 'input-file' or elem_type == 'output-file':
            pass
        else:
            raise Exception('Unknown type: {}'.format(elem_type))

        if len(restrictions) > 0 and restrictions[-1] == '':
            restrictions.pop()

        return restrictions

    def print_config(self, print_attributes=DEFAULT_PRINT_ATTRIBUTES, skipped_elements=DEFAULT_SKIPPED_ELEMENTS):
        elements = self.dom.getElementsByTagName('ITEM')
        for elem in elements:
            if elem.getAttribute('name') in skipped_elements:
                continue
            string = '{{{} : {}}}'.format('name', elem.getAttribute('name'))
            for attr in print_attributes[1:]:
                if elem.hasAttribute(attr):
                    string += ', {{{} : {}}}'.format(attr, elem.getAttribute(attr))
            restrictions = self.parse_restrictions(elem)
            string += ', {{restrictions : {}}}'.format(restrictions)
            log(string)
            print(string)

    def write_config(self, file_name):
        with open(file_name, 'w') as f:
            f.write(self.dom.toxml())

    def run_program(self, verbose=True):
        tries = 5
        while tries > 0:
            p = Popen(self.get_args(), stdout=PIPE)
            res = p.wait()
            output = p.stdout.read().decode()
            if verbose:
                log(output)
                print(output)
            if res != 0:
                log("Failed to run program, tries left {}".format(tries))
                print("Failed to run program, tries left {}".format(tries))
                tries -= 1
            else:
                return output

    def get_restrictions(self, name, offset=0):
        elem = self.get_element(name, offset)
        elem_type = elem.getAttribute('type')
        if elem_type != 'int' and elem_type != 'double':
            raise Exception("Type of {} is {}. "
                            "It is not available for optimising".format(elem.getAttribute('name'), elem_type))
        restrictions = self.parse_restrictions(elem)
        if len(restrictions) != 2:
            raise Exception("{} is not available for optimising. "
                            "It has no upper boundary in restrictions".format(elem.getAttribute('name')))
        if elem_type == 'int':
            for i in [0, 1]:
                restrictions[i] = int(restrictions[i])
            restrictions.append(1)
        else:
            restrictions = [float(restriction) for restriction in restrictions]
            restrictions.append((restrictions[1] - restrictions[0])/100)
        return restrictions

    def find_best_value(self, name, offset, *args):
        restrictions = self.get_restrictions(name, offset)

        self.write_config(self.working_ini_file)
        val = float(self.get_element(name, offset).getAttribute('value'))
        log("Trying with default: {} = {}...".format(name, val))
        print("Trying with default: {} = {}...".format(name, val))
        output = self.run_program(False)
        res = None
        try:
            res = self.get_result(output)
        except Exception as e:
            log("fail: {}".format(str(e)))
            print("fail: {}".format(str(e)))

        print("Result = {} with value = {}".format(res, val))
        log("Result = {} with value = {}".format(res, val))

        best_val = val
        best_res = res
        val = restrictions[0]
        step = restrictions[2]
        other_best = []
        other = []

        results = {}

        while val <= restrictions[1]:
            self.set_attribute(name, 'value', val, offset)
            self.write_config(self.working_ini_file)
            print("Trying {} = {}...".format(name, val))
            log("Trying {} = {}...".format(name, val))
            if len(args) > 0:
                res, other = self.find_best_value(args[0], args[1], args[2:] if len(args) > 2 else None)
            else:
                output = self.run_program(False)
                try:
                    res = self.get_result(output)
                except Exception as e:
                    print("fail: {}".format(str(e)))
                    log("fail: {}".format(str(e)))

            results[val] = res

            if self.cmp_result(res, best_res):
                best_res = res
                best_val = val
                other_best = other

            print("Result = {} with value = {}".format(res, val))
            log("Result = {} with value = {}".format(res, val))
            # print("Best = {} with value = {}".format(best_res, best_val))
            # log("Best = {} with value = {}".format(best_res, best_val))

            val += step

        if len(args) == 0:
            self.lower_bound = restrictions[0]
            self.upper_bound = restrictions[1]
            upper = False
            for val, res in sorted(results.items()):
                print(val, res)
                if upper:
                    if not self.low_result(res, best_res):
                        self.upper_bound = val
                else:
                    if not self.low_result(res, best_res):
                        self.lower_bound = val
                        upper = True

            self.set_attribute(name, 'restrictions', '{}:{}'.format(self.lower_bound, self.upper_bound), offset)
            self.set_attribute(name, 'value', best_val, offset)

        other_best.insert(0, best_val)
        return best_res, other_best

    @abc.abstractmethod
    def low_result(self, res, best):
        raise NotImplementedError

    @abc.abstractmethod
    def cmp_result(self, res, best):
        raise NotImplementedError

    @abc.abstractmethod
    def get_result(self, output):
        raise NotImplementedError

    @abc.abstractmethod
    def get_args(self):
        raise NotImplementedError

    def set_attribute(self, name, attr, value, offset):
        self.get_element(name, offset).setAttribute(attr, str(value))

    def run(self):
        for name, offset in self.optimisation_elements:
            try:
                print("Optimising {}".format(name, offset))
                log("Optimising {}".format(name, offset))
                res, val = self.find_best_value(name, offset)
                print("Best {} = {} with value = {}".format(name, res, val[0]))
                log("Best {} = {} with value = {}".format(name, res, val[0]))
                self.write_config("saved_config.ini")
            except Exception as e:
                print("Can not find best value for {}: {}".format(name, e))
                log("Can not find best value for {}: {}".format(name, e))


class FeatureFinderOptimiser(ConfigurationOptimiser):
    def __init__(self, config):
        ConfigurationOptimiser.__init__(self, config)
        self.optimisation_elements = [('mz_tolerance', 0), ('min_spectra', 0), ('max_missing', 0),
                                      ('slope_bound', 0),
                                      ('charge_low', 0), ('charge_high', 0), ('mz_tolerance', 1),
                                      ('intensity_percentage', 0), ('intensity_percentage_optional', 0),
                                      ('optional_fit_improvement', 0), ('mass_window_width', 0),
                                      ('abundance_12C', 0), ('abundance_14N', 0),
                                      ('min_score', 0), ('epsilon_abs', 0),
                                      ('min_score', 1), ('min_isotope_fit', 0), ('min_trace_score', 0),
                                      ('min_rt_span', 0), ('max_rt_span', 0), ('max_intersection', 0)]
        self.working_ini_file = WORKING_INI_FFC_FILE
        self.dom = xml.dom.minidom.parse(config.ffcini)

    def get_args(self):
        return self.config.ffc, '-in', self.config.mzml, '-out', DEFAULT_FFC_OUTPUT_FILE, '-ini', WORKING_INI_FFC_FILE

    def get_result(self, output):
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
        output = opt.run_program(False)
        return {'value': opt.get_result(output), 'time': t}
        # return opt.get_result(output)

    def cmp_result(self, res, best):
        return res['value'] > best['value'] or (res['value'] == best['value'] and res['time'] + 3 < best['time'])

    def low_result(self, res, best):
        return res['value'] < 0.99 * best['value']


class IDMapperOptimiser(ConfigurationOptimiser):
    def __init__(self, config):
        ConfigurationOptimiser.__init__(self, config)
        self.optimisation_elements = [('rt_tolerance', 0), ('mz_tolerance', 0)]
        self.working_ini_file = WORKING_INI_IDM_FILE
        self.dom = xml.dom.minidom.parse(config.idmini)

    def get_args(self):
        return (self.config.idm, '-in', DEFAULT_FFC_OUTPUT_FILE, '-out', DEFAULT_IDM_OUTPUT_FILE, '-id',
                self.config.idxml, '-ini', WORKING_INI_IDM_FILE)

    def get_result(self, output):
        m = re.search(r"Peptides assigned to exactly one feature: (\d*)", output)
        if m:
            return int(m.group(1))
        else:
            raise Exception("No result")

    def cmp_result(self, res, best):
        return res > best

    def low_result(self, res, best):
        return False


def parse_args():
    parser = argparse.ArgumentParser(description='Settings selection for FeatureFinderCentroided algorithm')
    parser.add_argument('-ffc', type=str, help='FeatureFinderCentroided executable')
    parser.add_argument('-ffcini', type=str, help='Settings ini file for FeatureFinderCentroided')
    parser.add_argument('-idm', type=str, help='IDMapper executable')
    parser.add_argument('-idmini', type=str, help='Settings ini file for IDMapper')
    parser.add_argument('-mzml', type=str, help='.mzML input file for FeatureFinderCentroided')
    parser.add_argument('-idxml', type=str, help='.idXML input file for IDMapper')
    return parser.parse_args()


def main():
    config = parse_args()
    opt = FeatureFinderOptimiser(config)
    # opt = IDMapperOptimiser(config)

    # opt.write_config(opt.working_ini_file)
    # output = opt.run_program()
    # res = opt.get_result(output)
    # print(res)

    while True:
        opt.run()

if __name__ == '__main__':
    main()