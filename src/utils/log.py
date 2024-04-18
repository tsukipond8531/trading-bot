import logging
from typing import Any


def init_logging() -> None:
    """Initialize logging component
    todo: return component_name: str = '' as argument when putting CMRESHandler back
    :param component_name: optional component name for identification in logs
    """

    # Get root logger
    root_logger = logging.getLogger()

    # Clear default handler
    root_logger.handlers = []

    # Default formatter
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')

    # Set default logging level for child loggers
    default_level = get_level('INFO')
    root_logger.setLevel(default_level)

    # Configure stdout handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(default_level)
    root_logger.addHandler(handler)

    # # Configure ElasticSearch handler
    # if config.ES_ENABLED in TRUE_VALUES:
    #     if (config.ES_USER != "") and (config.ES_PASS != ""):
    #         elastic_handler = CMRESHandler(
    #             hosts=[{'host': config.ES_HOST, 'port': config.ES_PORT}],
    #             auth_type=CMRESHandler.AuthType.BASIC_AUTH,
    #             auth_details=(config.ES_USER, config.ES_PASS),
    #             es_index_name=config.ES_INDEX,
    #             es_additional_fields={'component': component_name, 'component_id': uuid.uuid4()}
    #         )
    #     else:
    #         elastic_handler = CMRESHandler(
    #             hosts=[{'host': config.ES_HOST, 'port': config.ES_PORT}],
    #             auth_type=CMRESHandler.AuthType.NO_AUTH,
    #             es_index_name=config.ES_INDEX,
    #             es_additional_fields={'component': component_name, 'component_id': uuid.uuid4()}
    #         )
    #     elastic_level = get_level(config.ES_LEVEL)
    #     elastic_handler.setLevel(elastic_level)
    #     root_logger.addHandler(elastic_handler)

    # Configure file handler
    # if config.LOCAL_ENABLED in TRUE_VALUES:
    #     os.makedirs(config.LOCAL_DIR, exist_ok=True)
    #     file_handler = logging.FileHandler(os.path.join(config.LOCAL_DIR, config.LOCAL_FILE))
    #     file_handler.setFormatter(formatter)
    #     file_handler.setLevel(default_level)
    #     root_logger.addHandler(file_handler)

    # Turn off logging for third party libraries
    logging.getLogger('elasticsearch').setLevel(logging.ERROR)


def get_level(str_level: str) -> Any:
    """Get logging level

    :param str_level: string representation of logging level (e.g. DEBUG, INFO, ERROR, ...)
    :return: logging level as attribute of logging package
    """
    if not hasattr(logging, str_level):
        raise ValueError(f"Invalid logging level '{str_level}' in configuration")
    return getattr(logging, str_level)
