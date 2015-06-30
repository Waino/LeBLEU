#!/usr/bin/env python
from __future__ import unicode_literals

import argparse
import codecs
import sys
#from . import lebleu
import lebleu
import locale

def get_parser():
    parser = argparse.ArgumentParser(
        prog='LeBLEU',
        description="""
FIXME
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False)
    parser.add_argument('hypfile',
                        metavar='<hyp_file>',
                        help='Hypothesis file')
    parser.add_argument('reffile',
                        metavar='<ref_file>',
                        help='Reference file')

    parser.add_argument('-e', '--encoding', dest='encoding',
                        type=str, default=None,
                        help='Override encoding of locale.')

    parser.add_argument('-s', '--sentence', dest='sentence',
                        default=False, action='store_true',
                        help='Output sentence level score')
    parser.add_argument('-n', '--max-n', dest='max_n',
                        type=int, default=4,
                        help='Maximum hypothesis n-gram length. '
                             'Default "%(default)s").')
    parser.add_argument('-t', '--threshold', dest='threshold',
                        type=float, default=0.4,
                        help='Minimum proportion of matching characters '
                             'for the fuzzy matching. '
                             'Default "%(default)s").')
    parser.add_argument('-a', '--average', dest='average',
                        type=str, default='arithmetic',
                        choices=['arithmetic', 'geometric'],
                        help='Averaging method. '
                             'Default "%(default)s").')
    parser.add_argument('--smooth-average', dest='smooth',
                        default=False, action='store_true',
                        help='Smooth the n-gram scores to get non-zero '
                             'aggregate score with geometric mean. '
                             'Mainly useful for sentence level scores.')
    parser.add_argument('--sampling', dest='ngram_limit',
                        type=int, default=2000,
                        help='Approximate maximum number of n-grams '
                             'to collect. If the limit would be exceeded, '
                             'a regular sampling grid is applied to the '
                             'starting positions of the n-grams. '
                             'Default "%(default)s").')
    return parser


def strip_blanks(lines, fileid):
    blanks_encountered = False
    for line in lines:
        line = line.strip()
        if len(line) > 0:
            yield line
        else:
            if not blanks_encountered:
                print('WARNING: Blank lines in {}, removing'.format(fileid))
                blanks_encountered = True


def main(args):
    lb = lebleu.LeBLEU(
        max_n=args.max_n,
        threshold=args.threshold,
        ngram_limit=args.ngram_limit,
        average=args.average,
        smooth=args.smooth)

    if args.encoding is not None:
        encoding = args.encoding
    else:
        encoding = locale.getpreferredencoding()
    with codecs.open(args.reffile, 'r', encoding=encoding) as reffobj:
        with codecs.open(args.hypfile, 'r', encoding=encoding) as hypfobj:
            ref = strip_blanks(reffobj, 'reference')
            hyp = strip_blanks(hypfobj, 'hypothesis')
            if args.sentence:
                for (i, (h, r)) in enumerate(zip(hyp, ref)):
                    score = lb.eval_single(h, r)
                    print('{}\t{}'.format(i, score))
            else:
                score = lb.eval(hyp, ref)
                print('LeBLEU: {}'.format(score))


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args(sys.argv[1:])
    main(args)
