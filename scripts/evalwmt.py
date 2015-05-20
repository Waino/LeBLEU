#!/usr/bin/env python

import ast
import collections
import codecs
import glob
import locale
import logging
import os

#from mteval import *    # FIXME

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser(
        description="""Script for running MT evaluations for WMT data set""")
    parser.add_argument('-v', '--verbose', dest="verbose", type=int,
                        default=1, metavar='<int>',
                        help="verbose level (default %(default)s)")
    parser.add_argument('-e', '--encoding', metavar='<str>', type=str,
                        default=None, help='Override encoding of locale.')
    parser.add_argument('-m', '--metric', metavar='<str>', type=str,
                        default=None, help='metric function')
    parser.add_argument('-p', '--params', metavar='<str>', type=str,
                        default="{}",
                        help='dict of extra parameters for the metric')
    parser.add_argument('-n', '--name', metavar='<str>', type=str,
                        default="", help='override metric name (if not module name)')
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

    if args.encoding is not None:
        encoding = args.encoding
    else:
        encoding = locale.getpreferredencoding()

    assert args.metric is not None  # FIXME
    metrics = [(module, __import__(module))
               for module in args.metric.split(',')]

    kwparams = ast.literal_eval(args.params)

    trfiles = glob.glob(os.path.join(args.datadir,
                                     "system-outputs") + "/*/*/*")
    system_results = collections.defaultdict(dict)
    segment_results = collections.defaultdict(dict)
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

        with codecs.open(trfile, 'r', encoding=encoding) as fobj:
            hyps = [x.strip() for x in fobj.readlines()]

        with codecs.open(reffile, 'r', encoding=encoding) as fobj:
            refs = [x.strip() for x in fobj.readlines()]

        for (metric, module) in metrics:
            func = module.eval_single
            scores = [func(x, y, **kwparams) for x, y in zip(hyps, refs)]
            segment_results[metric][(dataset, lp, system)] = scores

            func = module.eval
            score = func(hyps, refs, **kwparams)[0]
            system_results[metric][(dataset, lp, system)] = score
            logging.info("%s" % score)


    if not os.path.isdir(args.outputdir):
        os.mkdir(args.outputdir)
    for (metric, module) in metrics:
        if args.name:
            name = args.name
        else:
            name = metric
        outfilename = os.path.join(args.outputdir, name+".system_level.scores") 
        with codecs.open(outfilename, 'w', encoding=encoding) as sysout:
            for k, score in system_results[metric].items():
                dataset, lp, system = k
                sysout.write("\t".join((name, lp, dataset, system, "%.6f" % score)) + "\n")

        outfilename = os.path.join(args.outputdir, name+".segment_level.scores")
        with codecs.open(outfilename, 'w', encoding=encoding) as segout:
            for k, scores in segment_results[metric].items():
                dataset, lp, system = k
                for i in range(len(scores)):
                    segout.write("\t".join((name, lp, dataset, system, str(i+1), "%.6f" % scores[i])) + "\n")

