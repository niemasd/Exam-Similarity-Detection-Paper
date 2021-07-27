#! /usr/bin/env python3
from csv import reader, writer
from gzip import open as gopen
from os.path import expanduser
from numpy import arange, log
from scipy.stats import expon, gaussian_kde, linregress
from sys import argv
if __name__ == "__main__":
    # parse user args
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', required=False, type=str, default='stdin', help="Input Similarity Score File (CSV)")
    parser.add_argument('-o', '--output', required=False, type=str, default='stdout', help="Output File (CSV)")
    parser.add_argument('-xm', '--xmin', required=True, type=float, help="Minimum Similarity Score")
    parser.add_argument('-xM', '--xmax', required=True, type=float, help="Maximum Similarity Score")
    parser.add_argument('-xd', '--xdelta', required=False, type=float, default=0.0001, help="Similarity Score Delta")
    args = parser.parse_args()

    # load similarity scores
    data = list()
    if args.input.lower() == 'stdin':
        from sys import stdin as infile
    elif args.input.lower().endswith('.gz'):
        infile = gopen(args.input, mode='rt')
    else:
        infile = open(args.input)
    for u,v,s in reader(infile):
        if s.strip() != 'Similarity':
            data.append((u.strip(),v.strip(),float(s)))

    # fit KDE using Gaussian kernels, regress best-fit line of log-PDF, and estimate Exponential dist
    kde = gaussian_kde([s for u,v,s in data])
    X = arange(args.xmin, args.xmax, args.xdelta)
    Y = log(kde.pdf(X))
    line = linregress(X,Y) # y = ln(L) - Lx, where L = rate parameter (lambda) of Exponential distribution
    rate = -1 * line.slope; scale = 1. / rate

    # output the input data, but with theoretical p-values added
    if args.output.lower() == 'stdout':
        from sys import stdout as outfile
    elif args.output.lower().endswith('.gz'):
        outfile = gopen(args.output, 'wt')
    else:
        outfile = open(args.output, 'w')
    try:
        outfile.write("Student 1,Student 2,Similarity,Distance From log-KDE Line,KDE p-value,Exponential p-value (rate=%f)\n" % rate)
        for u,v,s in data:
            dist = log(kde.pdf(s)) - (line.slope * s + line.intercept)
            p_kde = kde.integrate_box_1d(s, float('inf'))
            p_expon = 1. - expon.cdf(s, loc=0, scale=scale)
            outfile.write("%s,%s,%f,%f,%f,%f\n" % (u,v,s,dist,p_kde,p_expon))
        outfile.close()
    except BrokenPipeError:
        pass
