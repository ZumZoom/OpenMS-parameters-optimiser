import sys
import xml.etree.ElementTree as ET
import re


def get_identity(peptide):
    ret = str(peptide.attrib)
    hits = sorted(str(hit.attrib) for hit in peptide.iter('PeptideHit'))
    ret += str(hits)
    return ret


def erase_peptides(file_name, peptides):
    assert '.idXML' in file_name
    tree = ET.parse(file_name)
    root = tree.getroot()
    erased = 0
    for peptide in root.iter('PeptideIdentification'):
        identity = get_identity(peptide)
        if identity in peptides:
            root.remove(peptide)
            erased += 1
    if erased != len(peptides):
        print("WARNING\nErased {} peptides, but initial array contained {} peptides".format(erased, len(peptides)))
    tree.write(file_name)


def erase_features(file_name, feature_names):
    assert '.featureXML' in file_name
    tree = ET.parse(file_name)
    root = tree.getroot()
    erased = 0
    for feature in root.iter('feature'):
        feature_name = feature.get("id")
        if feature_name in feature_names:
            root.remove(feature)
            erased += 1
    if erased != len(feature_names):
        print("WARNING\nErased {} peptides, but initial array contained {} peptides".format(erased, len(feature_names)))
    tree.write(file_name)


def count_peptides(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()
    peptides = set()
    for peptide in root.iter('PeptideIdentification'):
        identity = get_identity(peptide)
        peptides.add(identity)
    print("Assigned peptides: %d" % len(peptides))
    peptides.clear()
    for peptide in root.iter('UnassignedPeptideIdentification'):
        identity = get_identity(peptide)
        peptides.add(identity)
    print("Unassigned peptides: %d" % len(peptides))


def get_data_to_delete(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()
    peptides = {}
    duplicates = {}
    # divergent = {}
    # identical = {}
    # single = {}
    # empty = {}
    features_to_delete = set()
    # peptides_to_delete = set()

    for feature in root.iter('feature'):
        feature_name = feature.get("id")
        cur_peptides = set()
        for peptide in feature.findall('PeptideIdentification'):
            identity = get_identity(peptide)

            if identity in cur_peptides:
                feature.remove(peptide)
                continue
            else:
                cur_peptides.add(identity)

            if identity in peptides.keys():
                if peptides[identity] != feature_name:
                    if identity in duplicates.keys():
                        duplicates[identity].append(feature_name)
                    else:
                        duplicates[identity] = [peptides[identity], feature_name]
            else:
                peptides[identity] = feature_name

    for peptide in root.findall('UnassignedPeptideIdentification'):
        identity = get_identity(peptide)
        if identity in peptides:
            root.remove(peptide)

    print("Peptides assigned to exactly one feature: %d" % (len(peptides) - len(duplicates)))
    print("Peptides assigned to multiply features: %d" % len(duplicates))

    for feature in root.iter('feature'):
        # feature_name = feature.get("id")
        local_peptides = set()
        peptides = set()
        peptides_count = 0
        good_feature = True
        for peptide in feature.iter('PeptideIdentification'):
            best_hit = None
            best_score = -1.0
            peptide_id = get_identity(peptide)
            for hit in peptide.iter('PeptideHit'):
                score = float(hit.get("score"))
                if score > best_score:
                    best_hit = hit
                    best_score = score

            peptides.add(peptide_id)

            if peptide_id in duplicates:
                good_feature = False

            seq = re.sub(r"\(.*?\)", "", best_hit.get("sequence"))
            identity = (seq, best_hit.get("charge"))
            peptides_count += 1
            local_peptides.add(identity)

        if good_feature and len(local_peptides) == 1:
            features_to_delete.add(feature)

        # if peptides_count > 1:
        #     if len(local_peptides) > 1:
        #         divergent[feature_name] = local_peptides
        #     elif len(local_peptides) == 1:
        #         identical[feature_name] = local_peptides
        # elif peptides_count == 1:
        #     single[feature_name] = local_peptides
        # else:
        #     empty[feature_name] = local_peptides

    # print("Peptides assigned to exactly one feature: %d" % (len(peptides) - len(duplicates)))
    # print("Peptides assigned to multiply features: %d" % len(duplicates))
    # print("\t no ID: %d" % len(empty))
    # print("\t single ID: %d" % len(single))
    # print("\t identical IDs: %d" % len(identical))
    # print("\t divergent IDs: %d" % len(divergent))

    print("Features to delete: %d" % len(features_to_delete))
    # print("Peptides to delete: %d" % len(peptides_to_delete))

    peptides_to_delete = set()
    for feature in features_to_delete:
        peptides = set()
        for peptide in feature.findall('PeptideIdentification'):
            peptide_id = get_identity(peptide)
            peptides.add(peptide_id)

        peptides_to_delete |= peptides
    print("Peptides to delete: %d" % len(peptides_to_delete))

    tree.write(file_name)

    return features_to_delete, peptides_to_delete


    # print("Divergent:")
    # for value in divergent.values():
    #     print(value)

    # dups = set((key[2], key[3]) for key in duplicates.keys())
    # divergs = set()
    # for val in divergent.values():
    #     divergs |= set(val)
    #
    # peptides = set()
    # unassigned = set()
    #
    # for peptide in root.iter('PeptideIdentification'):
    #     hit = peptide.find("PeptideHit")
    #     identity = (hit.get("sequence"), hit.get("charge"))
    #     if identity not in dups and identity not in divergs:
    #         peptides.add(identity)
    #     else:
    #         unassigned.add(identity)
    #
    # for peptide in root.iter('UnassignedPeptideIdentification'):
    #     hit = peptide.find("PeptideHit")
    #     identity = (hit.get("sequence"), hit.get("charge"), hit.get("score"))
    #     if identity not in peptides:
    #         unassigned.add(identity)
    #
    # print("Really unassigned peptides: %d" % len(unassigned))
    # print("Really uniquely assigned peptides: %d" % len(peptides))



    # print("Duplicate assignments: %d" % len(duplicates))
    # print("Features with divergent IDs: %d" % len(divergent))
    # print("Features with identical IDs: %d" % len(identical))
    # print("Features with single ID: %d" % len(single))
    # print("Features with no ID: %d" % len(empty))

    # divergent.sort()
    # print("Divergent:")
    # for value in divergent.values():
    #     print(value)

    # print("Identical:")
    # print(identical)

    # dups.sort()

    # print(unassigned)
    # print(len(dups))
    # print(len(set(dups)))


def main():
    # argv[1] - готовый featureXML
    # argv[2] - исходный idXML
    # argv[3] - исходный featureXML

    assert '.featureXML' in sys.argv[1]
    assert '.idXML' in sys.argv[2]
    assert '.featureXML' in sys.argv[3]

    features_to_delete, peptides_to_delete = get_data_to_delete(sys.argv[1])

####### save new features

    tree = ET.parse('saved_features.xml')
    root = tree.getroot()
    prev_features = set(root.findall('feature'))

    with open('saved_features.xml', 'w') as f:
        f.write(b'<featurelist>\n')
        for feature in features_to_delete:
            f.write(ET.tostring(feature))
        for feature in prev_features:
            f.write(ET.tostring(feature))
        f.write(b'\n</featurelist>')

#######

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()
    feature_list = root.find('featureList')
    for feature in feature_list.findall('feature'):
        feature_name = feature.get("id")

    # count_peptides(sys.argv[1])
    # print(peptides)
    # print("To remove:")
    # print(to_remove)


if __name__ == '__main__':
    main()