import sys
import xml.etree.ElementTree as ET
import re
import time


def get_identity(peptide):
    ret = str(peptide.attrib)
    hits = sorted(str(hit.attrib) for hit in peptide.iter('PeptideHit'))
    ret += str(hits)
    return ret


def erase_peptides(file_name, peptides):
    assert '.idXML' in file_name
    tree = ET.parse(file_name)
    root = tree.getroot().find('IdXML')
    erased = 0
    for peptide in root.findall('PeptideIdentification'):
        identity = get_identity(peptide)
        if identity in peptides:
            root.remove(peptide)
            erased += 1
    if erased != len(peptides):
        print("WARNING: erased {} peptides, but initial array contained {} peptides".format(erased, len(peptides)))
    tree.write(file_name)


def erase_features(file_name, feature_names):
    assert '.featureXML' in file_name
    tree = ET.parse(file_name)
    root = tree.getroot().find('featureList')
    erased = 0
    for feature in root.findall('feature'):
        feature_name = feature.get("id")
        if feature_name in feature_names:
            root.remove(feature)
            erased += 1
    if erased != len(feature_names):
        print("WARNING: erased {} features, but initial array contained {} features".format(erased, len(feature_names)))
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

    # clear a little
    tree.write(file_name)

    print("Peptides assigned to exactly one feature: %d" % (len(peptides) - len(duplicates)))
    print("Peptides assigned to multiply features: %d" % len(duplicates))

    features_to_delete = set()

    for feature in root.iter('feature'):
        local_peptides = set()
        good_feature = True
        for peptide in feature.iter('PeptideIdentification'):
            best_hit = None
            best_score = -1.0
            for hit in peptide.iter('PeptideHit'):
                score = float(hit.get("score"))
                if score > best_score:
                    best_hit = hit
                    best_score = score

            if get_identity(peptide) in duplicates:
                good_feature = False

            seq = re.sub(r"\(.*?\)", "", best_hit.get("sequence"))
            identity = (seq, best_hit.get("charge"))
            local_peptides.add(identity)

        if good_feature and len(local_peptides) == 1:
            features_to_delete.add(feature)

    print("Features to delete: %d" % len(features_to_delete))

    peptides_to_delete = set()
    for feature in features_to_delete:
        peptides = set()
        for peptide in feature.findall('PeptideIdentification'):
            peptide_id = get_identity(peptide)
            peptides.add(peptide_id)

        peptides_to_delete |= peptides
    print("Peptides to delete: %d" % len(peptides_to_delete))

    return features_to_delete, peptides_to_delete


def main():
    # argv[1] - готовый featureXML
    # argv[2] - исходный idXML
    # argv[3] - исходный featureXML

    assert '.featureXML' in sys.argv[1]
    assert '.idXML' in sys.argv[2]
    assert '.featureXML' in sys.argv[3]

    start = time.time()

    features_to_delete, peptides_to_delete = get_data_to_delete(sys.argv[1])
    features = {feature.get("id"): feature for feature in features_to_delete}

    print("Elapsed {} seconds".format(time.time() - start))

    for feat in features.keys():
        print(feat)

####### save new features

    start = time.time()

    prev_features = set()
    try:
        tree = ET.parse('saved_features.xml')
        root = tree.getroot()
        prev_features |= set(root.findall('feature'))
    except FileNotFoundError:
        pass

    with open('saved_features.xml', 'wb') as f:
        f.write(b'<featurelist>\n')
        for feature in features_to_delete:
            f.write(ET.tostring(feature))
        for feature in prev_features:
            f.write(ET.tostring(feature))
        f.write(b'\n</featurelist>')

    print("Elapsed {} seconds".format(time.time() - start))

#######

    start = time.time()

    erase_peptides(sys.argv[2], peptides_to_delete)

    print("Elapsed {} seconds".format(time.time() - start))

#######

    start = time.time()

    erase_features(sys.argv[3], features.keys())

    print("Elapsed {} seconds".format(time.time() - start))

####### create new optimal featureXML

    start = time.time()

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()
    feature_list = root.find('featureList')
    for feature in feature_list.findall('feature'):
        feature_name = feature.get("id")
        if feature_name in features.keys():
            feature_list.remove(feature)
            feature_list.append(features[feature_name])
    tree.write('optimal.featureXML')

    print("Elapsed {} seconds".format(time.time() - start))

if __name__ == '__main__':
    main()