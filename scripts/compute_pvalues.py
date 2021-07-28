#! /usr/bin/env python3
from csv import reader, writer
from gzip import open as gopen
from os.path import expanduser
from numpy import arange, log
from scipy.stats import expon, gaussian_kde, linregress
from sys import argv, stderr
VERSION = '1.0.0'

def print_stderr(s=''):
    print(s, file=stderr); stderr.flush()

def qvalues_bonferroni(pvalues, data):
    return [min(1, p*len(data)) for p in pvalues]

def qvalues_benjamini_hochberg(pvalues, data):
    sorted_unique_pvals = sorted(set(pvalues))
    rank = {p:(i+1) for i,p in enumerate(sorted_unique_pvals)}
    return [min(1, p*len(data)/rank[p]) for p in pvalues]

correction_funcs = {
    'bonferroni': qvalues_bonferroni,
    'benjamini_hochberg': qvalues_benjamini_hochberg,
}

if __name__ == "__main__":
    # parse user args
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', required=False, type=str, default='stdin', help="Input Similarity Score File (CSV)")
    parser.add_argument('-o', '--output', required=False, type=str, default='stdout', help="Output File (CSV)")
    parser.add_argument('-xm', '--xmin', required=True, type=float, help="Minimum Similarity Score")
    parser.add_argument('-xM', '--xmax', required=True, type=float, help="Maximum Similarity Score")
    parser.add_argument('-xd', '--xdelta', required=False, type=float, default=0.0001, help="Similarity Score Delta")
    parser.add_argument('-c', '--correction', required=False, type=str, default='benjamini_hochberg', help="p-Value Correction (options: %s)" % ', '.join(sorted(correction_funcs.keys())))
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose Mode")
    args = parser.parse_args()
    args.correction = args.correction.lower().replace('-','_').replace(' ','_')
    if args.correction in correction_funcs:
        correction = correction_funcs[args.correction]
    else:
        raise ValueError("Invalid correction method: %s (options: %s)" % (args.correction, ', '.join(sorted(correction_funcs.keys()))))
    if args.verbose:
        print_stderr("Exam Similarity Outlier Detection v%s (Niema Moshiri 2021)" % VERSION)

    # load similarity scores
    if args.verbose:
        print_stderr("Loading similarity scores from: %s" % args.input)
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
    if args.verbose:
        print_stderr("Computing Gaussian KDE...")
    kde = gaussian_kde([s for u,v,s in data])
    if args.verbose:
        print_stderr("Computing linear regression of log-KDE...")
    X = arange(args.xmin, args.xmax, args.xdelta)
    Y = log(kde.pdf(X))
    line = linregress(X,Y) # y = ln(L) - Lx, where L = rate parameter (lambda) of Exponential distribution
    rate = -1 * line.slope; scale = 1. / rate
    if args.verbose:
        print_stderr("Best-fit log-KDE line: y = %fx + %f" % (line.slope, line.intercept))
        print_stderr("Best-fit Exponential: rate = %f --> scale = 1/rate = %f" % (rate, scale))

    # compute p-values and q-values (corrected p-values)
    if args.verbose:
        print_stderr("Computing theoretical p-values...")
    pvals_expon = [1.-expon.cdf(s,loc=0,scale=scale) for u,v,s in data]
    if args.verbose:
        print_stderr("Computing q-values (corrected p-values) using: %s" % args.correction)
    qvals_expon = correction(pvals_expon, data)

    # output the input data, but with theoretical p-values added
    if args.verbose:
        print_stderr("Outputting results...")
    if args.output.lower() == 'stdout':
        from sys import stdout as outfile
    elif args.output.lower().endswith('.gz'):
        outfile = gopen(args.output, 'wt')
    else:
        outfile = open(args.output, 'w')
    try:
        outfile.write("Student 1,Student 2,Similarity,p-value (rate=%f),q-value (%s)\n" % (rate, args.correction))
        for i in range(len(data)):
            u,v,s = data[i]
            p_expon = pvals_expon[i]
            q_expon = qvals_expon[i]
            outfile.write("%s,%s,%f,%f,%f\n" % (u,v,s,p_expon,q_expon))
        outfile.close()
    except BrokenPipeError:
        pass
