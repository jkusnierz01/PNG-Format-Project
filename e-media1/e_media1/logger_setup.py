import logging
import colorlog




def setup_color_logging():
    # Konfiguracja handlera dla colorlog
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white'
        }))

    # Konfiguracja loggera colorlog
    logger = colorlog.getLogger("loger")
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger