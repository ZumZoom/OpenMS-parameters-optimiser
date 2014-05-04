import sys
import xml.etree.ElementTree as ET
import re


def erase_peptides(file_name, peptides):
    tree = ET.parse(file_name)
    root = tree.getroot()
    erased = 0
    for peptide in root.iter('PeptideIdentification'):
        identity = (float(peptide.get("RT")), float(peptide.get("MZ")))
        if identity in peptides:
            root.remove(peptide)
            erased += 1
    if erased != len(peptides):
        print("WARNING\nErased {} peptides, but initial array contained {} peptides".format(erased, len(peptides)))


def get_unique_peptides(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()
    peptides = {}
    duplicates = {}
    divergent = {}
    identical = {}
    single = {}
    empty = {}

    for feature in root.iter('feature'):
        feature_name = feature.get("id")
        for peptide in feature.iter('PeptideIdentification'):
            hit = peptide.find("PeptideHit")
            seq = re.sub(r"\(.*?\)", "", hit.get("sequence"))
            identity = (float(peptide.get("RT")), float(peptide.get("MZ")), seq, hit.get("charge"), hit.get("score"))
            if identity in peptides.keys():
                if peptides[identity] != feature_name:
                    if identity in duplicates.keys():
                        duplicates[identity].append(feature_name)
                    else:
                        duplicates[identity] = [peptides[identity], feature_name]
            else:
                peptides[identity] = feature_name

        local_peptides = []
        peptides_count = 0
        for peptide in feature.iter('PeptideIdentification'):
            hit = peptide.find("PeptideHit")
            seq = re.sub(r"\(.*?\)", "", hit.get("sequence"))
            seq = ''.join(sorted(seq))
            identity = (seq, hit.get("charge"))
            peptides_count += 1
            if identity not in local_peptides:
                local_peptides.append(identity)
        if peptides_count > 1:
            if len(local_peptides) > 1:
                divergent[feature_name] = local_peptides
            elif len(local_peptides) == 1:
                identical[feature_name] = local_peptides
        elif peptides_count == 1:
            single[feature_name] = local_peptides
        else:
            empty[feature_name] = local_peptides

    dups = []
    for key, value in duplicates.items():
        identity = (key[2], key[3])
        dups.append(identity)

    divergs = []
    for key, value in divergent.items():
        divergs.append(key)

    peptides = []
    unassigned = []

    for peptide in root.iter('PeptideIdentification'):
        hit = peptide.find("PeptideHit")
        seq = re.sub(r"\(.*?\)", "", hit.get("sequence"))
        identity = (seq, hit.get("charge"))
        if identity not in peptides and identity not in dups and identity not in divergs:
            peptides.append(identity)
        elif (identity in dups and identity not in unassigned) or (identity in divergs and identity not in unassigned):
            unassigned.append(identity)

    for peptide in root.iter('UnassignedPeptideIdentification'):
        hit = peptide.find("PeptideHit")
        seq = re.sub(r"\(.*?\)", "", hit.get("sequence"))
        identity = (seq, hit.get("charge"))
        if identity not in peptides and identity not in unassigned:
            unassigned.append(identity)

    print("Unassigned peptides: %d" % len(unassigned))
    print("Peptides assigned: %d" % len(peptides))
    print("Duplicate assignments: %d" % len(duplicates))
    print("Features with divergent IDs: %d" % len(divergent))
    print("Features with identical IDs: %d" % len(identical))
    print("Features with single ID: %d" % len(single))
    print("Features with no ID: %d" % len(empty))

    # divergent.sort()
    print("Divergent:")
    for value in divergent.values():
        print(value)

    # print("Identical:")
    # print(identical)

    # dups.sort()

    # print(unassigned)
    # print(len(dups))
    # print(len(set(dups)))


def main():
    get_unique_peptides(sys.argv[1])
    # print(peptides)
    # print("To remove:")
    # print(to_remove)


if __name__ == '__main__':
    main()