# core/trend_logger.py

def log_trend(logger, name, data):
    """
    Loguje szczegółowe dane trendu (1H lub 1D).
    """
    logger.info(f"TREND {name}:")
    for key, value in data.items():
        logger.info(f" - {key}: {value}")
