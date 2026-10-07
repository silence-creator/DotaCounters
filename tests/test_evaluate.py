"""Оценка драфта: пары с двух сторон, итог, линии, мета. Сеть не нужна."""

import unittest

from dotacounters.dotabuff import MIN_MATCHES, Matchup
from dotacounters.evaluate import evaluate, pair_value


class Report:
    def __init__(self, rows):
        self.matchups = [Matchup(hero=h, win_rate="50.00%", advantage_value=v,
                                 matches=m if m is not None else 50000)
                         for h, v, *rest in rows for m in (rest[0] if rest else None,)]


class PairTest(unittest.TestCase):

    def test_sign_from_our_page(self):
        # Со страницы Anti-Mage: Medusa ему «−9,5» — это он её контрит
        reports = {"Anti-Mage": Report([("Medusa", -9.5)])}
        self.assertEqual(pair_value("Anti-Mage", "Medusa", reports)[0], 9.5)

    def test_sign_from_their_page(self):
        # Со страницы Medusa: Anti-Mage ей «+9,5» — он её контрит, для нас плюс
        reports = {"Medusa": Report([("Anti-Mage", 9.5)])}
        self.assertEqual(pair_value("Anti-Mage", "Medusa", reports)[0], 9.5)

    def test_both_pages_are_averaged(self):
        reports = {"A": Report([("B", -2.0)]), "B": Report([("A", 4.0)])}
        self.assertEqual(pair_value("A", "B", reports)[0], 3.0)

    def test_rare_pair_counts_as_zero(self):
        reports = {"A": Report([("B", -8.0, MIN_MATCHES - 1)])}
        self.assertEqual(pair_value("A", "B", reports)[0], 0.0)

    def test_no_data(self):
        self.assertIsNone(pair_value("A", "B", {}))


class EvaluateTest(unittest.TestCase):
    # Позиции — из снимка линий с понятными героями
    LANES = {
        "Carry": {"safe": (90.0, 600)}, "Mid": {"mid": (90.0, 550)},
        "Off": {"off": (90.0, 500)}, "Four": {"off": (80.0, 350)},
        "Five": {"safe": (80.0, 330)},
        "ECarry": {"safe": (90.0, 600)}, "EMid": {"mid": (90.0, 550)},
        "EOff": {"off": (90.0, 500)},
    }

    def test_score_is_sum_over_five(self):
        reports = {"Carry": Report([("EOff", -5.0), ("EMid", 1.0)])}
        result = evaluate(["Carry", "Mid"], ["EOff", "EMid"], reports, lanes=self.LANES)
        self.assertAlmostEqual(result.score, (5.0 - 1.0) / 5)
        self.assertEqual(result.unknown, ["Mid"], "по Mid ни одной пары")
        self.assertEqual([p.theirs for p in result.best()], ["EOff"])
        self.assertEqual([p.theirs for p in result.worst()], ["EMid"])

    def test_lanes_by_positions(self):
        reports = {"Carry": Report([("EOff", -5.0)]), "Mid": Report([("EMid", 2.0)]),
                   "Off": Report([("ECarry", -1.0)])}
        result = evaluate(["Carry", "Mid", "Off", "Four", "Five"], ["ECarry", "EMid", "EOff"],
                          reports, lanes=self.LANES)
        lanes = {lane.lane: lane for lane in result.lanes}
        self.assertEqual(lanes["safe"].ours, ["Carry", "Five"])
        self.assertEqual(lanes["safe"].theirs, ["EOff"])
        self.assertEqual(lanes["safe"].value, 5.0)
        self.assertEqual(lanes["mid"].value, -2.0)
        self.assertEqual(lanes["off"].value, 1.0)

    def test_meta_average(self):
        meta = {"Carry": ((10.0, 52.0),) * 5, "ECarry": ((10.0, 48.0),) * 5}
        result = evaluate(["Carry"], ["ECarry"], {}, meta=meta, lanes=self.LANES)
        self.assertEqual(result.meta, (52.0, 48.0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
