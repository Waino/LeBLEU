from __future__ import division, unicode_literals

import collections

NGramProps = collections.namedtuple('NGramProps', ['count', 'length', 'hits'])

def make_acceptor(n, limit):
    acc_ratio = limit / n
    if acc_ratio < 0.5:
        m = n // limit
        return lambda i: i % m == 0
    else:
        m = n // (n - limit)
        return lambda i: i % m < (m-1)

def ngrams(seq, max_n, min_n=1, limit=None):
    assert min_n > 0
    len_seq = len(seq)
    if limit is not None and limit < len_seq:
        acc = make_acceptor(len_seq, limit)
    else:
        acc = lambda i: True
    staggered = [seq[n:] for n in range(max_n)]
    for _ in range(max_n - min_n + 1):
        for (i, ngram) in enumerate(zip(*staggered)):
            if acc(i):
                yield ngram
        staggered.pop()

class LeBLEU(object):
    """LeBLEU: Soft BLEU score based on letter edits / Levenshtein distance"""
    pass

