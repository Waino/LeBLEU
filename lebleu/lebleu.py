from __future__ import division, unicode_literals

import collections
#import harry
import Levenshtein
import scipy
import numpy as np


def make_acceptor(n, limit):
    acc_ratio = limit / n
    #print('acc_ratio {}'.format(acc_ratio))
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


def best_scores(scores, sortidx, ref_counts, count):
    """sum together the best scores, taking reference counts into account"""
    out = 0.0
    cursor = -1     # best scores at end of sorted matrix
    while count > 0:
        score = scores[sortidx[cursor]]
        if score == 0:
            # early exit if no more hits to be found
            return out
        refc = ref_counts[sortidx[cursor]]
        refc = min(refc, count)
        out += refc * score
        #print('adding {} * {} = {}'.format(refc, score, refc * score))
        count -= refc
        cursor -= 1
    return out


class BLEU(object):
    def __init__(self,
                 max_n=3,
                 ngram_limit=None,
                 average='arithmetic',
                 smooth=False):
        self.max_n = max_n
        self.ngram_limit = ngram_limit
        self.smooth = smooth
        if self.ngram_limit <= 0:
            self.ngram_limit = None
        if average == 'arithmetic':
            self.mean = np.mean
        elif average == 'geometric':
            self.mean = scipy.stats.mstats.gmean
        else:
            raise Exception('Unknown averaging method "{}"'.format(average))

    def count_ngrams(self, tokens, max_n=None):
        if max_n is None:
            max_n = self.max_n
        ngramcounts = collections.Counter()
        if self.ngram_limit is not None:
            limit = self.ngram_limit // max_n
            #print('limit {}'.format(limit))
        else:
            limit = None
        for ngram in ngrams(tokens, max_n, min_n=1, limit=limit):
            ngramcounts[ngram] += 1
        return ngramcounts

    def eval_single(self, hypothesis, reference):
        # FIXME not implemeted yet
        pass

    def penalty(self, hyplen, reflen):
        return min(1.0, np.exp(1.0 - (reflen / hyplen)))

    def combine_scores(self, hits, tot, hyplen, reflen):
        if self.smooth:
            hits = self._smooth(hits)
        precisions = hits / tot
        # FIXME: warn when dropping nans?
        precisions = precisions[~np.isnan(precisions)]
        avg = self.mean(precisions)
        penalty = self.penalty(hyplen, reflen)
        return penalty * avg

    def _smooth(self, hits):
        """The smoothing is computed by replacing a 0 hit score
        with 1 / ( 2^k ), where k is the distance from the last
        n-gram length with non-zero hits.
        """
        last = None
        for (i, h) in enumerate(hits):
            if h == 0:
                if last is None:
                    last = i - 1
                hits[i] = 1. / 2**(i - last)
        return hits

class LeBLEU(BLEU):
    """LeBLEU: Soft BLEU score based on letter edits / Levenshtein distance"""
    def __init__(self,
                 max_n=3,
                 threshold=0.4,
                 ngram_limit=2000,
                 average='arithmetic',
                 smooth=False):
        super(LeBLEU, self).__init__(max_n,
                                     ngram_limit,
                                     average,
                                     smooth)
        self.threshold = threshold

    def distances(self, hyp, ref, bestonly):
        #return harry.compare(hyp, ref, measure='levenshtein')
        bo = 1 if bestonly else 0
        dist = Levenshtein.compare_lists(hyp, ref, self.threshold, bo)
        # replace special value -1 meaning "above threshold"
        dist[dist == -1] = np.NaN
        return dist

    def _eval_helper(self, hypothesis, reference):
        hyp_words = hypothesis.split()
        ref_words = reference.split()

        hyp_ngrams = self.count_ngrams(hyp_words).items()
        ref_ngrams = self.count_ngrams(ref_words,
                                       max_n=(2 * self.max_n)
                                      ).items()
        # separate n-grams for which 1-best is enough
        hyp_ngrams_single = [(h, c) for (h, c) in hyp_ngrams if c == 1]
        hyp_ngrams_multi  = [(h, c) for (h, c) in hyp_ngrams if c > 1]
        hyp_strs_single = [' '.join(h) for (h, c) in hyp_ngrams_single]
        hyp_strs_multi  = [' '.join(h) for (h, c) in hyp_ngrams_multi]
        
        ref_strs = [' '.join(r) for (r, _) in ref_ngrams]

        hyp_ngrams = hyp_ngrams_single + hyp_ngrams_multi
        hyp_strs = hyp_strs_single + hyp_strs_multi

        scores_single = self.distances(hyp_strs_single, ref_strs, True)
        if len(hyp_strs_multi) > 0:
            scores_multi = self.distances(hyp_strs_multi, ref_strs, False)
            scores = np.concatenate((scores_single, scores_multi))
        else:
            scores = scores_single

        #print(scores)
        scores = self._score(scores, hyp_strs, ref_strs)
        #print(scores)

        sortidx = scores.argsort()
        ref_counts = [count for (_, count) in ref_ngrams]

        hits = np.zeros(self.max_n)
        tot = np.zeros(self.max_n)
        for (i, item) in enumerate(hyp_ngrams):
            hyp, count = item
            order = len(hyp)
            # sum together the count best scores
            hits[order - 1] += best_scores(scores[i],
                                           sortidx[i],
                                           ref_counts,
                                           count)
            tot[order - 1] += count
            #print(i, hits, tot, hyp)
        return (hits, tot)

    def eval_single(self, hypothesis, reference):
        (hits, tot) = self._eval_helper(hypothesis, reference)
        score = self.combine_scores(hits,
                                    tot,
                                    len(hypothesis),
                                    len(reference))

        return score

    def eval(self, hyps, refs):
        hits = np.zeros(self.max_n)
        tot = np.zeros(self.max_n)
        hyplen = 0
        reflen = 0
        for hyp, ref in zip(hyps, refs):
            hyplen += len(hyp)
            reflen += len(ref)
            (h, t) = self._eval_helper(hyp, ref)
            #print('h {} t {}'.format(h, t))
            hits += h
            tot += t
        score = self.combine_scores(hits,
                                    tot,
                                    hyplen,
                                    reflen)
        return score

    def _score(self, dist, hyp, ref):
        num_hyps = len(hyp)
        num_refs = len(ref)

        # matrix of lengths (in chars) of the longer
        # of the two compared strings, for normalization
        ngram_lens = np.zeros((2, num_hyps, num_refs))
        ngram_lens[0] += np.array(
            [len(h) for h in hyp],
            ndmin=2).T
        ngram_lens[1] += np.array(
            [len(r) for r in ref],
            ndmin=2)
        ngram_lens = ngram_lens.max(axis=0)

        # distance normalized by said maxlength, negated so bigger is better
        score = 1.0 - (dist / ngram_lens)
        # set lower-bound pruned comparisons to zero score
        score[np.isnan(score)] = 0
        # if the normalized distance is too far, no score is awarded
        score[score < self.threshold] = 0
        return score
