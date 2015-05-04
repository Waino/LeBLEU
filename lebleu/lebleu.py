from __future__ import division, unicode_literals

import collections
import harry
import numpy as np

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
    def __init__(self, max_n=3, threshold=0.4, ngram_limit=2000):
        self.max_n = max_n
        self.threshold = threshold
        self.ngram_limit = ngram_limit

    def count_ngrams(self, tokens):
        ngramcounts = collections.Counter()
        limit = self.ngram_limit // self.max_n
        for ngram in ngrams(tokens, self.max_n, min_n=1, limit=limit):
            ngramcounts[ngram] += 1
        return ngramcounts

    def distances(self, hyp, ref):
        return harry.compare(hyp, ref, measure='levenshtein')

    def eval_single(self, hypothesis, reference):
        hyp_words = hypothesis.split()
        ref_words = reference.split()

        hyp_ngrams = self.count_ngrams(hyp_words).items()
        hyp_strs = [' '.join(h) for (h, _) in hyp_ngrams]
        ref_ngrams = self.count_ngrams(ref_words).items()   # FIXME: up to 2n
        ref_strs = [' '.join(r) for (r, _) in ref_ngrams]

        score = self.distances(hyp_strs, ref_strs)
        print(score)
        score = self._score(score, hyp_strs, ref_strs)
        print(score)
        score.sort()    # FIXME: breaks if ref count other than 1
        print(score)

        hits = np.zeros(self.max_n)
        tot = np.zeros(self.max_n)
        for (i, item) in enumerate(hyp_ngrams):
            hyp, count = item
            order = len(hyp)
            # sum together the count best scores    # FIXME: breaks if ref count other than 1
            hits[order - 1] += sum(score[i, -count:])
            print('{} best: {}'.format(count, score[i, -count:]))
            tot[order - 1] += count
            print(i, hits, tot, hyp)
        precisions = hits / tot

        return precisions

    def _score(self, dist, hyp, ref):
        num_hyps = len(hyp)
        num_refs = len(ref)

        # matrix of lengths (in chars) of the longer of the compared strings
        ngram_lens = np.zeros((2, num_hyps, num_refs))
        ngram_lens[0] += np.array(
            [len(h) for h in hyp],
            ndmin=2).T
        ngram_lens[1] += np.array(
            [len(r) for r in ref],
            ndmin=2)
        ngram_lens = ngram_lens.max(axis=0)

        # distance normalized by said maxlength, negated so bigger is better
        score = 1.0 - dist / ngram_lens
        # if the normalized distance is too far, no score is awarded
        score[score < self.threshold] = 0
        return score

