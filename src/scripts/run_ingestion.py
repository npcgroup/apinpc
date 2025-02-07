from dexscreener_ingestion import DataIngestion as DexScreenerIngestion
from hypurrscan_ingestion import HypurrscanIngestion
from flipside_ingestion import FlipsideIngestion
import logging

logger = logging.getLogger(__name__)

def run_all_ingestion():
    try:
        # Run DexScreener ingestion
        logger.info("Starting DexScreener ingestion...")
        dex_ingestion = DexScreenerIngestion()
        token_metrics = dex_ingestion.ingest_token_data()
        if token_metrics:
            dex_ingestion.save_results(token_metrics)
        
        # Run Hypurrscan ingestion
        logger.info("Starting Hypurrscan ingestion...")
        hyp_ingestion = HypurrscanIngestion()
        for token in hyp_ingestion.tokens:
            holders = hyp_ingestion.get_token_holders(token)
            if holders['holders']:
                hyp_ingestion.save_results(holders, f'{token.lower()}_holders')
        
        # Run Flipside ingestion
        logger.info("Starting Flipside ingestion...")
        flip_ingestion = FlipsideIngestion()
        metrics = flip_ingestion.get_metrics()
        if metrics:
            flip_ingestion.save_metrics(metrics)
        
        logger.info("All ingestion processes completed successfully")
        
    except Exception as e:
        logger.error(f"Error in ingestion process: {str(e)}")
        raise

if __name__ == "__main__":
    run_all_ingestion() 