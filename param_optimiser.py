import argparse
import shutil
from feature_finder_optimiser import FeatureFinderOptimiser
from id_mapper_optimiser import IDMapperOptimiser
from constants import *

__author__ = 'zumzoom'


def files(s):
    try:
        return s.split()
    except:
        raise argparse.ArgumentTypeError("files should be divided by commas")


def parse_args():
    parser = argparse.ArgumentParser(description='Settings selection for FeatureFinderCentroided algorithm')
    parser.add_argument('-ffc', type=str, help='FeatureFinderCentroided executable')
    parser.add_argument('-ffcini', type=str, help='Settings ini file for FeatureFinderCentroided')
    parser.add_argument('-idm', type=str, help='IDMapper executable')
    parser.add_argument('-idmini', type=str, help='Settings ini file for IDMapper')
    parser.add_argument('-mzml', type=files, help='.mzML input file for FeatureFinderCentroided')
    parser.add_argument('-idxml', type=str, help='.idXML input file for IDMapper')
    return parser.parse_args()


def main():
    config = parse_args()
    shutil.copy(config.ffcini, SAVED_INI_FFC_FILE)
    shutil.copy(config.idmini, SAVED_INI_IDM_FILE)
    opt = FeatureFinderOptimiser(config)
    opt1 = IDMapperOptimiser(config)

    # opt.write_config(opt.working_ini_file)
    # output = opt.run_program()
    # res = opt.get_result(output)
    # print(res)

    best_opt = 0
    best_opt1 = 0
    increased = True
    while increased:
        increased = False
        new_opt = opt.run()
        new_opt1 = opt1.run()
        if best_opt < new_opt:
            best_opt = new_opt
            increased = True
        if best_opt1 < new_opt1:
            best_opt1 = new_opt1
            increased = True

if __name__ == '__main__':
    main()
