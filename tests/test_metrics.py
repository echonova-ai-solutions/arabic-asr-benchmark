import random

import jiwer
import pytest

from arabic_asr_benchmark.metrics import CorpusScore, macro_average, score_corpus, score_utterance


def test_perfect():
    u = score_utterance("a b c", "a b c")
    assert (u.word_errors, u.sub, u.dele, u.ins, u.char_errors) == (0, 0, 0, 0, 0)


def test_sub_del_ins():
    u = score_utterance("a b c", "a x c")
    assert (u.sub, u.dele, u.ins, u.word_errors) == (1, 0, 0, 1)
    u = score_utterance("a b c", "a c")
    assert (u.sub, u.dele, u.ins) == (0, 1, 0)
    u = score_utterance("a b c", "a b c d")
    assert (u.sub, u.dele, u.ins) == (0, 0, 1)


def test_empty_hypothesis_is_full_deletion():
    u = score_utterance("a b c", "")
    assert (u.dele, u.word_errors, u.empty_hyp) == (3, 3, True)
    assert u.char_errors == len("a b c")


def test_empty_reference_counts_insertions():
    u = score_utterance("", "x y")
    assert (u.ref_words, u.ins, u.word_errors) == (0, 2, 2)


def test_corpus_is_micro_not_mean_of_utterances():
    utts = [score_utterance("a", "b"), score_utterance("a b c d e f g h i j", "a b c d e f g h i j")]
    c = score_corpus(utts)
    assert c.wer == pytest.approx(1 / 11)
    assert c.wer != pytest.approx((1.0 + 0.0) / 2)


def test_zero_length_corpus_raises():
    c = score_corpus([score_utterance("", "x")])
    with pytest.raises(ValueError):
        _ = c.wer
    with pytest.raises(ValueError):
        _ = CorpusScore().cer
    with pytest.raises(ValueError):
        macro_average([])


def test_cer_counts_spaces():
    u = score_utterance("ab cd", "abcd")
    assert (u.ref_chars, u.char_errors) == (5, 1)


def test_macro_vs_micro():
    a = score_corpus([score_utterance("a b c d", "a b c d")])  # 0 / 4
    b = score_corpus([score_utterance("a", "b")])  # 1 / 1
    both = score_corpus([score_utterance("a b c d", "a b c d"), score_utterance("a", "b")])
    assert both.wer == pytest.approx(0.2)
    assert macro_average([a.wer, b.wer]) == pytest.approx(0.5)


def test_matches_jiwer_on_random_text():
    rng = random.Random(0)
    vocab = ["كتاب", "قلم", "بيت", "ولد", "a", "b"]
    refs, hyps = [], []
    for _ in range(300):
        refs.append(" ".join(rng.choice(vocab) for _ in range(rng.randint(1, 12))))
        hyps.append(" ".join(rng.choice(vocab) for _ in range(rng.randint(0, 12))))
    c = score_corpus(score_utterance(r, h) for r, h in zip(refs, hyps, strict=False))
    out = jiwer.process_words(refs, hyps)
    assert c.word_errors == out.substitutions + out.deletions + out.insertions
    assert c.sub + c.dele + c.ins == c.word_errors
    assert c.cer == pytest.approx(jiwer.cer(refs, hyps))


def test_to_dict():
    d = score_corpus([score_utterance("a b", "a")]).to_dict()
    assert d["del"] == 1 and "dele" not in d and d["wer"] == 0.5
