from subprocess import Popen, PIPE
import abc
import re
from logger import log
from constants import *
from timer import Timer

__author__ = 'zumzoom'


class ConfigurationOptimiser():
    __metaclass__ = abc.ABCMeta
    optimisation_elements = []

    def __init__(self, config):
        self.dom = None
        self.config = config
        self.optimisation_elements = []
        self.working_ini_file = None
        self.ini_to_save = None
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
    def equal(a, b):
        return abs(a - b) < EPS


    @staticmethod
    def parse_restrictions(elem):
        elem_type = elem.getAttribute('type')
        restrictions = []
        value = None
        if elem_type == 'string':
            restrictions = re.split(',', elem.getAttribute('restrictions'))
        elif elem_type == 'int' or elem_type == 'double':
            restrictions = re.split(':', elem.getAttribute('restrictions'))
            value = float(elem.getAttribute('value'))
        elif elem_type == 'input-file' or elem_type == 'output-file':
            pass
        else:
            raise Exception('Unknown type: {}'.format(elem_type))

        if len(restrictions) > 0 and restrictions[-1] == '':
            restrictions.pop()

        if elem_type == 'int' or elem_type == 'double':
            if len(restrictions) == 0:
                restrictions.append(0)
            if len(restrictions) == 1:
                restrictions.append(value * 100)

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

    @staticmethod
    def run_program(args, verbose=True):
        tries = 5
        while tries > 0:
            p = Popen(args, stdout=PIPE)
            res = p.wait()
            output = p.stdout.read().decode()
            if verbose:
                log(output)
                # print(output)
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
            restrictions.append((restrictions[1] - restrictions[0])/20)
        return restrictions

    def find_best_value(self, name, offset):
        restrictions = self.get_restrictions(name, offset)

        self.write_config(self.working_ini_file)
        val = float(self.get_element(name, offset).getAttribute('value'))
        log("Trying with default: {} = {}...".format(name, val))
        print("Trying with default: {} = {}...".format(name, val))
        res = None
        for i in range(len(self.config.mzml)):
            t = Timer()
            t.start()
            output = self.run_program(self.get_args(i), False)
            print('run_program took %.2f sec' % t.get())
            try:
                t.start()
                tmp_res = self.get_result(output, i)
                print('get_result took %.2f sec' % t.get())
                res = self.add_res(res, tmp_res) if res is not None else tmp_res
            except Exception as e:
                log("fail: {}".format(str(e)))
                print("fail: {}".format(str(e)))

        print("Result = {} with value = {}".format(res, val))
        log("Result = {} with value = {}".format(res, val))

        best_val = val
        best_res = res

#        other_best = []
#        other = []

        results = dict()
        results[val] = res

        def one_search(low, up, step, depth=0):
            nonlocal best_res
            nonlocal best_val
            val = low
            increased = False
            while val <= up:
                if val in results:
                    val += step
                    continue
                self.set_attribute(name, 'value', val, offset)
                self.write_config(self.working_ini_file)
                print("Trying {} = {}...".format(name, val))
                log("Trying {} = {}...".format(name, val))
                res = None
                for i in range(len(self.config.mzml)):
                    t = Timer()
                    t.start()
                    output = self.run_program(self.get_args(i), False)
                    print('run_program took %.2f sec' % t.get())

                    try:
                        t.start()
                        tmp_res = self.get_result(output, i)
                        print('get_result took %.2f sec' % t.get())
                        res = self.add_res(res, tmp_res) if res is not None else tmp_res
                    except Exception as e:
                        print("fail: {}".format(str(e)))
                        log("fail: {}".format(str(e)))

                if res is not None:
                    results[val] = res

                print("Result = {} with value = {}".format(res, val))
                log("Result = {} with value = {}".format(res, val))

                if res is not None and self.cmp_result(res, best_res):
                    best_res = res
                    best_val = val
                    increased = True

                    # if self.get_element(name, offset).getAttribute('type') != 'int' and depth < MAX_REC_DEPTH:
                    #     print("We need to go deeper with low = {}, high = {}, step = {}"
                    #           "".format(max(val - step * 0.8, low + step / 5),
                    #                     min(val + step * 0.8, up - step / 5), step / 5))
                    #     log("We need to go deeper with low = {}, high = {}, step = {}"
                    #         "".format(max(val - step * 0.8, low + step / 5),
                    #                   min(val + step * 0.8, up - step / 5), step / 5))
                    #     one_search(max(val - step * 0.8, low + step / 5), min(val + step * 0.8, up - step / 5),
                    #                step / 5, depth + 1)
                    # other_best = other

                # print("Best = {} with value = {}".format(best_res, best_val))
                # log("Best = {} with value = {}".format(best_res, best_val))

                val += step

            if increased and depth < MAX_REC_DEPTH:
                print("We need to go deeper with low = {}, high = {}, step = {}"
                      "".format(max(best_val - step * 0.8, low + step / 5),
                                min(best_val + step * 0.8, up - step / 5), step / 5))
                log("We need to go deeper with low = {}, high = {}, step = {}"
                    "".format(max(best_val - step * 0.8, low + step / 5),
                              min(best_val + step * 0.8, up - step / 5), step / 5))
                one_search(max(best_val - step * 0.8, low + step / 5),
                           min(best_val + step * 0.8, up - step / 5), step / 5, depth + 1)

        one_search(restrictions[0], restrictions[1], restrictions[2])

#        if len(args) == 0:
        self.lower_bound = restrictions[0]
        self.upper_bound = restrictions[1]
        for val, res in sorted(results.items()):
            print(val, res)

        candidate = restrictions[0]
        for val, res in sorted(results.items()):
            if not self.low_result(res, best_res):
                self.lower_bound = candidate
                break
            candidate = val

        candidate = restrictions[1]
        for val, res in sorted(results.items())[::-1]:
            if not self.low_result(res, best_res):
                self.upper_bound = candidate
                break
            candidate = val

        print("restrictions: {}, {}".format(self.lower_bound, self.upper_bound))
        log("restrictions: {}, {}".format(self.lower_bound, self.upper_bound))

        self.set_attribute(name, 'restrictions', '{}:{}'.format(self.lower_bound, self.upper_bound), offset)
        self.set_attribute(name, 'value', best_val, offset)

#        other_best.insert(0, best_val)
        return best_res, best_val  # , other_best

    @abc.abstractmethod
    def low_result(self, res, best):
        raise NotImplementedError

    @abc.abstractmethod
    def cmp_result(self, res, best):
        raise NotImplementedError

    @abc.abstractmethod
    def get_result(self, output, i):
        raise NotImplementedError

    @abc.abstractmethod
    def get_args(self, i=0):
        raise NotImplementedError

    def set_attribute(self, name, attr, value, offset):
        self.get_element(name, offset).setAttribute(attr, str(value))

    @abc.abstractmethod
    def pre_loading(self):
        raise NotImplementedError

    @abc.abstractmethod
    def add_res(self, res1, res2):
        raise NotImplementedError

    def run(self):
        self.pre_loading()

        best = 0

        for name, offset in self.optimisation_elements:
            try:
                print("Optimising {}".format(name, offset))
                log("Optimising {}".format(name, offset))
                res, val = self.find_best_value(name, offset)
                best = max(best, res)
                print("Best {} = {} with value = {}".format(name, res, val))
                log("Best {} = {} with value = {}".format(name, res, val))
                self.write_config(self.ini_to_save)
            except Exception as e:
                print("Can not find best value for {}: {}".format(name, e))
                log("Can not find best value for {}: {}".format(name, e))

        return best
