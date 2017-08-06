#!/usr/bin/env python
import boto3
import sys
import json
import logging
from botocore.exceptions import ClientError
from CoinCollection import ValueRecord

logger = logging.getLogger("tango")
logger.setLevel(logging.DEBUG)

class Cache():

    def stash(self, key, record):
        logger.debug("Stash request for: " + key)
        self.getTable().delete_item(
            Key={
                'coin_type': key
            }
        )
        self.getTable().put_item(
            Item={
                'coin_type': key,
                'value_record': record.serialize()
            }
        )

    def retrieve(self, key):
        try:
            logger.debug("Retrieving record for: " + key)
            response = self.getTable().get_item(
                Key={
                    'coin_type': key,
                }
            )
        except ClientError as e:
            errorMsg = e.response['Error']['Message']
            logger.error(errorMsg)
            raise ValueError("Unable to retrieve for : " + key + " due to client error.")
        else:
            try:
                rec = response['Item']['value_record']
                logger.debug("Response was: " + rec)
                return ValueRecord(key,'USD',0.0).fromJSON(rec)
            except (KeyError) as kerr:
                return None

    def expired(self, key):
        expired = True
        try:
            logger.debug("Expiration check for: " + key)
            expired = self.retrieve(key).expired()
        except (ValueError, AttributeError) as verr:
            logger.error("Error occured checking expiration: " + str(verr))
            expired = True
        return expired

    def getTable(self):
        try:
            self.table
        except AttributeError:
            self.table = self.getDB().Table('tango_cache')
        return self.table

    def getDB(self):
        try:
            self.dynamodb
        except AttributeError:
            self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1') #, endpoint_url="http://localhost:8000")
        return self.dynamodb

    def createTangoCache(self):
        table = self.getDB().create_table(
            TableName='tango_cache',
            KeySchema=[
                {
                    'AttributeName': 'coin_type',
                    'KeyType': 'HASH'  #Partition key
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'coin_type',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )

        print("Table status:", table.table_status)

if __name__ == '__main__':
    if (len(sys.argv) > 1):
        if sys.argv[1] == 'createcache':
            Cache().createTangoCache()
