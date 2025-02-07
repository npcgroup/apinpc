import pytest
from src.data.processing.funding_processor import FundingRateAnalyzer

def test_funding_processor():
    analyzer = FundingRateAnalyzer()
    assert analyzer is not None 