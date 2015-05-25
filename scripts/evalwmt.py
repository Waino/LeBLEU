#!/usr/bin/env python

import ast
import collections
import codecs
import glob
import locale
import logging
import re
import os
import sys

RE_LANG_PAIR = re.compile(r'^([a-z][a-z])-([a-z][a-z])$')

def metadata_from_name(trfile):
    path, basename = os.path.split(trfile)
    pathparts = path.split("/")
    sysparts = []
    lp = None
    dataset = None
    for namepart in basename.split('.'):
        if len(namepart) == 0:
            continue
        m = RE_LANG_PAIR.match(namepart)
        if m:
            if lp is not None:
                logging.warn('AMBIGUOUS LANGPAIR: "{}" or "{}"'.format(
                    namepart, lp))
            lp = namepart
            l1, l2 = m.groups()
            continue
        if namepart in pathparts:
            if dataset is not None:
                logging.warn('AMBIGUOUS DATASET: "{}" or "{}"'.format(
                    namepart, dataset))
            dataset = namepart
            continue
        sysparts.append(namepart)
    return dataset, lp, l1, l2, '.'.join(sysparts)

if __name__ == "__main__":
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

    trfiles = glob.glob(
        os.path.join(args.datadir, "system-outputs")
        + "/*/*/*")
    system_results = collections.defaultdict(dict)
    segment_results = collections.defaultdict(dict)
    for trfile in trfiles:
        try:
            # lp: language pair
            dataset, lp, l1, l2, system = metadata_from_name(trfile)
        except ValueError:
            logging.warning("Skipping %s" % trfile)
            continue

        logging.info('{} , {} , {} ({})'.format(dataset, lp, system, kwparams))
        reffile = os.path.join(args.datadir,
                               "references",
                               '{}-ref.{}'.format(dataset, l2))
        if not os.path.exists(reffile):
            reffile = os.path.join(args.datadir,
                                   "references",
                                   '{}-ref.{}'.format(dataset, lp))
        if not os.path.exists(reffile):
            logging.warning("Skipping %s due to lack of ref" % trfile)
            continue
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
            score = func(hyps, refs, **kwparams)
            system_results[metric][(dataset, lp, system)] = score
            logging.info("%s" % score)


    if not os.path.isdir(args.outputdir):
        os.mkdir(args.outputdir)
    for (metric, module) in metrics:
        if args.name:
            name = args.name
        else:
            name = metric
        sysoutputdir = os.path.join(args.outputdir, name)
        if not os.path.isdir(sysoutputdir):
            os.mkdir(sysoutputdir)
        outfilename = os.path.join(sysoutputdir,
                                   name + ".sys.score")
        with codecs.open(outfilename, 'w', encoding=encoding) as sysout:
            for k, score in system_results[metric].items():
                dataset, lp, system = k
                sysout.write(
                    "\t".join((name, lp, dataset, system, "%.6f" % score)))
                sysout.write("\n")

        outfilename = os.path.join(sysoutputdir,
                                   name + ".seg.score")
        with codecs.open(outfilename, 'w', encoding=encoding) as segout:
            for k, scores in segment_results[metric].items():
                dataset, lp, system = k
                for i in range(len(scores)):
                    segout.write("\t".join(
                        (name, lp, dataset, system,
                         str(i + 1), "%.6f" % scores[i])))
                    segout.write("\n")

