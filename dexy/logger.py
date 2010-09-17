import logging
import logging.handlers

log = logging.getLogger("dexy")
log.setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler("logs/dexy.log")
log.addHandler(handler) 

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

