import logging

logger = logging.getLogger("uvicorn")

def trigger_erp_sync(internship_id: str):
    """
    Mock ERP/Viva API trigger. 
    In production, this would make an HTTP request to an external system.
    """
    logger.info(f"[MOCK ERP TRIGGER] Syncing Internship {internship_id} to ERP/Viva System... SUCCESS")
