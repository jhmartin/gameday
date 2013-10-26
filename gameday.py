#!/usr/bin/python
import boto.sqs
import sys
import os
import signal
import daemonize
import lockfile
from ConfigParser import SafeConfigParser
import logging 
from daemonize import Daemonize
from time import sleep
import statsd

import logging
from daemonize import Daemonize

pid = "/root/gameday.pid"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh = logging.FileHandler("/root/gameday.log", "w+")
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]
parser = SafeConfigParser()
parser.read('/root/gameday.ini')
c = statsd.StatsClient('172.31.14.12',8125)

#tion.set_defaults(host='172.31.14.12',port=8126,disabled=False)



def main():
    conn = boto.sqs.connect_to_region(parser.get('gameday', 'region'),aws_access_key_id=parser.get('gameday', 'access_key'),aws_secret_access_key=parser.get('gameday', 'secret_key'))
    #statsd_client = statsd.Client(__name__,statsd_connection)
    #guage = statsd.Guage('MyApp')
    my_queue = conn.get_queue(parser.get('gameday', 'queue'))
    logger.debug(conn)
    logger.debug(my_queue)
    while True:
	#http://docs.pythonboto.org/en/latest/sqs_tut.html#reading-messages
	logger.debug("Currently " + str(my_queue.count()) + ' in queue')
	c.gauge('QueueDepth',my_queue.count())
	rs = my_queue.get_messages(num_messages=10)
	c.gauge('BatchSize',rs.__len__())
	logger.debug("Got " + str(len(rs)) + " messages")
	with c.timer('BatchTime'):
		for m in rs:
			with c.timer('Processtime'):
				logger.debug("Message: " + m.get_body())
				my_queue.delete_message(m)

daemon = Daemonize(app="test_app", pid=pid, action=main, keep_fds=keep_fds)
daemon.start()
#main()
