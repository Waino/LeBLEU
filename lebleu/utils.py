def ngrams(seq, max_n, min_n=1):
    assert min_n > 0
    staggered = [seq[n:] for n in range(max_n)]
    for _ in range(max_n - min_n + 1):
        for ngram in zip(*staggered):
            yield ngram
        staggered.pop()
