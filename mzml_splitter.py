import re

__author__ = 'zumzoom'

FILE_NAME = "for_test.mzML"

with open(FILE_NAME) as f:
    lines = f.readlines()

prefix = []
suffix = "\t\t</spectrumList>\n\t</run>\n</mzML>\n"
spectrum_list = '\t\t<spectrumList count="{}" defaultDataProcessingRef="dp_sp_0">\n'

regex = re.compile('\t\t<spectrumList count="(\d*)" defaultDataProcessingRef="dp_sp_0">')

prefix_done = False
parts = 100
count = 0
inside_count = 0
sz = 0

f = open('{}.mzML'.format(count), "w")

for line in lines:
    if count == parts:
        break

    if '<spectrumList' in line:
        m = regex.match(line)
        if m:
            sz = int(m.group(1))
        prefix_done = True

        for pref in prefix:
            f.write(pref)
        f.write(spectrum_list.format(sz // parts))
        continue

    if not prefix_done:
        prefix.append(line)
    else:
        f.write(line)
        if '<spectrum ' in line:
            inside_count += 1
        elif '</spectrum>' in line:
            if inside_count == sz // parts or (count + 1 == parts and inside_count == sz % parts):
                f.write(suffix)
                f.close()
                count += 1
                if count != parts:
                    f = open('{}.mzML'.format(count), "w")
                    for pref in prefix:
                        f.write(pref)
                    if count + 1 != parts:
                        f.write(spectrum_list.format(sz // parts))
                    else:
                        f.write(spectrum_list.format(sz % parts))
                inside_count = 0