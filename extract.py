import sys
import xml.etree.ElementTree as ET

__author__ = 'zumzoom'


def rec(root):
    res = []
    for child in root:
        if child.get('name') == 'debug':
            continue
        if child.tag == 'NODE':
            for i in rec(child):
                res.append((child.get('name') + ':' + i[0], i[1], i[2], i[3]))
        else:
            if child.get('type') == 'int':
                t = 'i'
                restr = child.get('restrictions').split(':')
                r = '({}, {})'.format(restr[0], restr[1] if restr[1] != '' else 100)
                val = child.get('value')
            elif child.get('type') == 'double':
                t = 'r'
                restr = child.get('restrictions').split(':')
                r = '({}, {})'.format(restr[0], restr[1] if restr[1] != '' else 100)
                val = child.get('value')
            else:
                t = 'c'
                r = '({})'.format(child.get('restrictions'))
                val = '"' + child.get('value') + '"'
            res.append((child.get('name'), t, r, val))
    return res


def main():
    root = ET.parse(sys.argv[1]).getroot()

    lst = []
    for i in rec(root.find('NODE').find('NODE').find('NODE')):
        lst.append(('algorithm:' + i[0], i[1], i[2], i[3]))

    # print parameters
    with open("parameters", "w") as f:
        for i in lst:
            f.write("{} {} {} {}\n".format(i[0].split(':')[-2] + ':' + i[0].split(':')[-1],
                                           '"-{} "'.format(i[0]), i[1], i[2]))
    #print candidates
    with open("candidates", "w") as f:
        for i in lst:
            f.write("{} ".format(i[0].split(':')[-2] + ':' + i[0].split(':')[-1]))
        f.write("\n")
        for i in lst:
            f.write("{} ".format(i[3]))
        f.write("\n")

    for t in range(2, len(sys.argv)):
        lst = []
        for i in rec(root.find('NODE').find('NODE').find('NODE')):
            lst.append(('algorithm:' + i[0], i[1], i[2], i[3]))

        #print candidates
        with open("candidates", "a") as f:
            for i in lst:
                f.write("{} ".format(i[0].split(':')[-2] + ':' + i[0].split(':')[-1]))
            f.write("\n")
            for i in lst:
                f.write("{} ".format(i[3]))
            f.write("\n")


if __name__ == '__main__':
    main()