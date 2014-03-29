import re
import sys

__author__ = 'zumzoom'

with open(sys.argv[1]) as f:
    lines = f.readlines()

features = re.compile(r"Peptides assigned to exactly one feature: (\d*)")
timing_s = re.compile(r"FeatureFinderCentroided took (\d*\.?\d*) s \(wall\)")
timing_m = re.compile(r"FeatureFinderCentroided took (\d\d):(\d\d) m \(wall\)")

val = 0
t = 0
for line in lines:
    m = features.search(line)
    if m:
        val = int(m.group(1))
        continue
    m = timing_s.search(line)
    if m:
        t = int(m.group(1))
        continue
    m = timing_s.search(line)
    if m:
        t = int(m.group(1)) * 60 + int(m.group(2))
        continue

print(-((val + 1) * 10000 - t))