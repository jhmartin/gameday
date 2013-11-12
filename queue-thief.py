#!/usr/bin/env python
import sys
import boto.sqs

sqs_conn = boto.connect_sqs(aws_access_key_id='AKIAJLPTH4N6KYF4UY4A',aws_secret_access_key='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')
while True:
    queues = sqs_conn.get_all_queues()
    for q in queues:
        messages = q.get_messages(10,visibility_timeout=900)
        for m in messages:
            print 'got message %s' % m