import pytest
from src.data.ingestion.funding_pipeline import FundingPipeline

def test_funding_pipeline_initialization():
    pipeline = FundingPipeline()
    assert pipeline is not None 