from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from src.data.ingestion.hyperliquid_funding import HyperliquidFundingCollector
from src.utils.database import SupabaseSync
from src.models.funding.analyzer import FundingRateAnalyzer 