import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.config import get_settings
from src.services.opensearch.client import OpenSearchClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pipeline():
    settings = get_settings()
    host = settings.opensearch.host
    client = OpenSearchClient(host, settings)
    
    logger.info(f"Testing RRF pipeline creation with host {host}")
    try:
        # Force recreation to test the perform_request call
        result = client._create_rrf_pipeline(force=True)
        logger.info(f"Pipeline creation result: {result}")
        if result:
            print("SUCCESS: RRF pipeline created/updated successfully.")
        else:
            print("INFO: Pipeline already exists or no change needed (but no error raised).")
    except Exception as e:
        logger.error(f"Pipeline creation failed: {e}")
        print(f"FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_pipeline()
