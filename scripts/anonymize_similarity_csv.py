#! /usr/bin/env python3
from csv import reader
from os.path import expanduser
from sys import argv
if __name__ == "__main__":
    if len(argv) != 3:
        print("Usage: %s <input_csv> <output_csv>" % argv[0]); exit(1)
    mask = dict(); out = open(expanduser(argv[2]), 'w')
    for u,v,s in reader(open(expanduser(argv[1]))):
        if s.strip() == 'Similarity':
            continue
        u = u.strip(); v = v.strip()
        if u not in mask:
            mask[u] = len(mask)
        if v not in mask:
            mask[v] = len(mask)
        out.write('%d,%d,%s\n' % (mask[u],mask[v],s))
    out.close()
