#!/usr/bin/python
import boto.sqs
import sys
import getopt
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

#Configure default options
configfile = "gameday.ini"
foreground = False

try:
	opts, args = getopt.getopt(sys.argv[1:],"hfc:",["configfile="])
except getopt.GetoptError:
	print sys.argv[0] + ' -h help, -c configfile, -f foreground'
	sys.exit(2)
for opt, arg in opts:
	if opt == '-h':
		print sys.argv[0] + ' -h help, -c configfile, -f foreground'
		sys.exit()
	elif opt in ("-c", "--config"):
		configfile = arg
	elif opt in ("-f","--foreground"):
		foreground = True

#Load the config file
parser = SafeConfigParser()
parser.read(configfile)

pid = parser.get('gameday', 'pidfile')
c = statsd.StatsClient(parser.get('gameday', 'statsd'),8125)

def main():
	#Configure logging
	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	fh.setFormatter(formatter)
	fh.setLevel(logging.DEBUG)
	logger = logging.getLogger(__name__)
	logger.addHandler(fh)
	logger.setLevel(logging.DEBUG)
	logger.propagate = False

	#setup SQS connection
	conn = boto.sqs.connect_to_region(parser.get('gameday', 'region'),aws_access_key_id=parser.get('gameday', 'access_key'),aws_secret_access_key=parser.get('gameday', 'secret_key'))
	my_queue = conn.get_queue(parser.get('gameday', 'queue'))
	logger.debug(conn)
	logger.debug(my_queue)

	#Start processing queue inputs
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

if foreground == True:
	fh = logging.StreamHandler()
	main()
else:
	fh = logging.FileHandler(parser.get('gameday', 'logfile'), "w+")
	keep_fds = [fh.stream.fileno()]
	daemon = Daemonize(app="gameday_app", pid=pid, action=main, keep_fds=keep_fds)
	daemon.start()
