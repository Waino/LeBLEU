#!/usr/bin/env python

import argparse
import sys
#from . import lebleu
import lebleu

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
    return parser

def main(args):
    lb = lebleu.LeBLEU() #ngram_limit=-1)
    with open(args.reffile, 'r') as reffobj:
        with open(args.hypfile, 'r') as hypfobj:
           ref = (line.strip() for line in reffobj)
           hyp = (line.strip() for line in hypfobj)
           score = lb.eval(hyp, ref)
    print('LeBLEU: {}'.format(score))


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args(sys.argv[1:])
    main(args)
