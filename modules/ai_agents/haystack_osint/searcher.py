import logging
from modules.database import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OSINTSearcher")

class OSINTSearcher:
    def __init__(self, db_config):
        self.db = db_manager.DatabaseManager(db_config)
        logger.info("OSINT Searcher initialized.")

    def search(self, query):
        try:
            logger.info(f"Searching for: '{query}' in index...")
            results = self.db.search_documents("osint_index", query)
            logger.info(f"Found {len(results)} results.")
            return results
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return []

    def find_relationships(self, entity):
        logger.info(f"Analyzing relationships for entity: '{entity}'...")
        return self.search(entity)