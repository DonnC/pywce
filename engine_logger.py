import logging
import logging.config

from logging.handlers import RotatingFileHandler

def get_engine_logger(name):
    _lg = logging.getLogger(name)

    _handler = RotatingFileHandler('pywce_engine.log', 'a', maxBytes=10*1024*1024, backupCount=7)
    _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    _handler.setFormatter(_formatter)
    _lg.addHandler(_handler)

    return _lg
