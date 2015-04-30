from __future__ import division, unicode_literals

import collections
import harry

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
    def __init__(self, max_n=3, ngram_limit=2000):
        self.max_n = max_n
        self.ngram_limit = ngram_limit

    def count_ngrams(self, tokens):
        ngramcounts = collections.Counter()
        limit = self.ngram_limit // self.max_n
        for ngram in ngrams(tokens, self.max_n, min_n=2, limit=limit):
            ngramcounts[ngram] += 1
        return ngramcounts

    def distances(self, hyp, ref):
        hyp = [' '.join(h) for (h, _) in hyp]
        ref = [' '.join(r) for (r, _) in ref]
        return harry.compare(hyp, ref, measure='levenshtein')

    def eval_single(self, hypothesis, reference):
        hyp_words = hypothesis.split()
        ref_words = reference.split()

        hyp_ngrams = self.count_ngrams(hyp_words).items()
        ref_ngrams = self.count_ngrams(ref_words).items()

        dist = self.distances(hyp_ngrams, ref_ngrams)
        return hyp_ngrams, ref_ngrams, dist # FIXME

