import re
import sys

__author__ = 'zumzoom'

with open(sys.argv[1]) as f:
    lines = f.readlines()

features = re.compile(r"Peptides assigned to exactly one feature: (\d*)")

val = 0

for line in lines:
    m = features.search(line)
    if m:
        val = int(m.group(1))
		print(-val)
		break



