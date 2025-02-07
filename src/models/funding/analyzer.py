import ccxt
from datetime import datetime
import os
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from tabulate import tabulate

from src.utils.database import SupabaseSync
from src.utils.logger import logger 

# Update data paths
self.data_dir = "data/analysis/funding" 