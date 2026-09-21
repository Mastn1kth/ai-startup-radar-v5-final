import logging

logger = logging.getLogger(__name__)


def init_sentry(dsn: str = "", environment: str = "development") -> bool:
    if not dsn:
        logger.info("SENTRY_DSN not set — Sentry disabled")
        return False

    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=0.1,
        )
        logger.info("Sentry initialized for environment: %s", environment)
        return True
    except Exception as e:
        logger.warning("Failed to initialize Sentry: %s", e)
        return False
