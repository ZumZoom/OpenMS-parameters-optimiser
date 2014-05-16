import argparse
import shutil
from constants import *
from features_extractor import features_extractor
from id_mapper_optimiser import IDMapperOptimiser

__author__ = 'zumzoom'


class FinalOptimiser(IDMapperOptimiser):
    def get_args(self, i=0):
        return (self.config.idm, '-in', self.config.inf, '-out', DEFAULT_IDM_OUTPUT_FILE, '-id',
                self.config.idxml, '-ini', WORKING_INI_IDM_FILE)

    def pre_loading(self):
        pass


def files(s):
    try:
        return s.split()
    except:
        raise argparse.ArgumentTypeError("files should be divided by commas")


def parse_args():
    parser = argparse.ArgumentParser(description='Settings selection for FeatureFinderCentroided algorithm')
    parser.add_argument('-idm', type=str, help='IDMapper executable')
    parser.add_argument('-idmini', type=str, help='Settings ini file for IDMapper')
    parser.add_argument('-idxml', type=str, help='.idXML input file for IDMapper')
    parser.add_argument('-inf', type=str, help='.featureXML input file for IDMapper')
    parser.add_argument('-mzml', type=files, help='.mzML input file for FeatureFinderCentroided')
    return parser.parse_args()


def main():
    config = parse_args()
    shutil.copy(config.idmini, SAVED_INI_IDM_FILE)

    while True:
        shutil.copy(config.idmini, SAVED_INI_IDM_FILE)
        opt = FinalOptimiser(config)
        best_opt = 0
        increased = True
        while increased:
            increased = False
            new_opt = opt.run()
            if best_opt < new_opt:
                best_opt = new_opt
                increased = True
        opt.write_config(WORKING_INI_IDM_FILE)
        opt.run_program(opt.get_args(False))
        if not features_extractor(DEFAULT_IDM_OUTPUT_FILE, config.idxml, config.inf, True):
            break


if __name__ == '__main__':
    main()
