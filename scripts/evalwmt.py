#!/usr/bin/env python

import os
import subprocess, shlex
import glob
import ast
import logging

from mteval import *    # FIXME

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser(
        description="""Script for running MT evaluations for WMT data set""")
    parser.add_argument('-v', '--verbose', dest="verbose", type=int,
                        default=1, metavar='<int>',
                        help="verbose level (default %(default)s)")
    parser.add_argument('-m', '--metric', metavar='<str>', type=str,
                        default="ler", help='metric function')
    parser.add_argument('-p', '--params', metavar='<str>', type=str,
                        default="{}",
                        help='dict of extra parameters for the metric')
    parser.add_argument('-n', '--name', metavar='<str>', type=str,
                        default="", help='metric name (if not function name)')
    parser.add_argument('datadir', metavar='<dir>', type=str,
                        help='WMT submissions directory')
    parser.add_argument('-o', '--outputdir', metavar='<dir>', type=str,
                        default='.', help='output directory')
    args = parser.parse_args()

    if args.verbose >= 2:
        loglevel = logging.DEBUG
    elif args.verbose >= 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING

    logging.basicConfig(format='%(module)s: %(message)s',
                        level=loglevel)

    kwparams = ast.literal_eval(args.params)
    if args.name:
        name = args.name
    else:
        name = metric

    metrics = args.metric.split(',')
    trfiles = glob.glob(os.path.join(args.datadir,
                                     "system-outputs") + "/*/*/*")
    system_results = {}
    segment_results = {}
    for trfile in trfiles:
        try:
            # lp: language pair
            dataset, lp, system = os.path.split(trfile)[1].split(".")
        except ValueError:
            logging.warning("Skipping %s" % trfile)
            continue

        l1, l2 = lp.split("-")
        logging.info("%s %s %s" % (dataset, lp, system))
        reffile = os.path.join(args.datadir,
                               "references",
                               dataset+"-ref."+l2)
        logging.info("%s" % reffile)
        logging.info("%s" % trfile)

        #with open(trfile, 'r') as fobj:
        #    hyps = [x.strip() for x in fobj.readlines()]
        p = subprocess.Popen(shlex.split("iconv -f utf-8 -t iso8859-1//TRANSLIT"), stdin=subprocess.PIPE, stdout=subpro
+cess.PIPE)
        with open(trfile, 'r') as fobj:
            p.stdin.write(bytes(fobj.read(), 'utf-8'))
        p.stdin.close()
        hyps = [x.decode("iso8859-1").strip() for x in p.stdout.readlines()]
        p.terminate()

        #with open(reffile, 'r') as fobj:
        #    refs = [x.strip() for x in fobj.readlines()]
        p = subprocess.Popen(shlex.split("iconv -f utf-8 -t iso8859-1//TRANSLIT"), stdin=subprocess.PIPE, stdout=subpro
+cess.PIPE)
        with open(reffile, 'r') as fobj:
            p.stdin.write(bytes(fobj.read(), 'utf-8'))
        p.stdin.close()
        refs = [x.decode("iso8859-1").strip() for x in p.stdout.readlines()]
        p.terminate()

        for metric in metrics:
            if not metric in system_results:
                system_results[metric] = {}
            if not metric in segment_results:
                segment_results[metric] = {}

            if metric in dir():
                func = eval(metric)
                scores = [func(x, y, **kwparams) for x, y in zip(hyps, refs)]
                segment_results[metric][(dataset, lp, system)] = scores

            system_metric = metric+"_a"
            if system_metric in dir():
                func = eval(system_metric)
                score = func(hyps, refs, **kwparams)[0]
                system_results[metric][(dataset, lp, system)] = score
                logging.info("%s" % score)


    if not os.path.isdir(args.outputdir):
        os.mkdir(args.outputdir)
    for metric in metrics:
        with open(os.path.join(args.outputdir, name+".system_level.scores"), 'w') as sysout:
            for k, score in system_results[metric].items():
                dataset, lp, system = k
                sysout.write("\t".join((name, lp, dataset, system, "%.6f" % score)) + "\n")

        with open(os.path.join(args.outputdir, name+".segment_level.scores"), 'w') as segout:
            for k, scores in segment_results[metric].items():
                dataset, lp, system = k
                for i in range(len(scores)):
                    segout.write("\t".join((name, lp, dataset, system, str(i+1), "%.6f" % scores[i])) + "\n")

