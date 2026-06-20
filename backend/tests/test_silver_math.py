import pytest
from app.services.silver_service import calculate_cagr

class TestCAGR:
    def test_basic_doubling(self):
        # 100 -> 200 over 1 period = 100% CAGR
        assert abs(calculate_cagr([100, 200]) - 1.0) < 0.001

    def test_three_year_growth(self):
        # 100 -> 133.1 over 3 periods ≈ 10% CAGR
        result = calculate_cagr([100, 110, 121, 133.1])
        assert abs(result - 0.10) < 0.01

    def test_empty_list_returns_none(self):
        assert calculate_cagr([]) is None

    def test_single_element_returns_none(self):
        assert calculate_cagr([100]) is None

    def test_negative_start_returns_none(self):
        assert calculate_cagr([-100, 200]) is None

    def test_negative_end_returns_none(self):
        assert calculate_cagr([100, -50]) is None

    def test_zero_start_returns_none(self):
        assert calculate_cagr([0, 100]) is None
