import logging
import logging.config
from concurrent_log_handler import ConcurrentRotatingFileHandler
import json
import os
import sys
from datetime import datetime, timezone

def make():

	level_object_json = {
		'DEBUG': logging.DEBUG,
		'INFO': logging.INFO,
		'WARNING': logging.WARNING,
		'ERROR': logging.ERROR,
		'CRITICAL': logging.CRITICAL,
	}

	file_handler = ConcurrentRotatingFileHandler(
		os.environ['WAY_TO_LOG_JOURNAL'],
		maxBytes=10485760,
		backupCount=3,
		encoding='utf-8',
		delay=True,
		use_gzip=True,
	)

	logging.basicConfig(
		handlers=[
			file_handler,
			logging.StreamHandler(),
		],
		level=level_object_json[os.environ['LEVEL_CONFIG']],
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
	)