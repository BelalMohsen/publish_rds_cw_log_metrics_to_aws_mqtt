"""
Python3 Module to publish log metrics from Cloudwatch to the AWS MQTT broker. An MQTT client can ingest these
log metrics and store them as time series data.
For our use case OpenNMS was the MQTT client and it stored the data in Cassandra.

Triggers on an metrics log event from Cloudwatch (Stream Log Group to Lambda)
Uncompress the log stream and decode it to a string
Enrich it with IP address data
Send it as a bytearray to the MQTT Broker topic aws-rds-data

Created: 24/06/2018 by chewborg @ RIPE NCC and iNOG hackathon 18

"""
import gzip
import logging
import json
import boto3
from io import BytesIO
import base64
from dns import resolver as dns


region = 'eu-west-1'  # set your region. required for iot
mqtt_topic = 'aws-rds-data'  # set you mqtt topic to publish to
mqtt_endpoint = ''  # used with logging only

iot_client = boto3.client('iot-data', region_name=region)  # set your region
rds_client = boto3.client('rds', region_name=region)


def setup_logging():
    logger = logging.getLogger('rds_metrics_to_mqtt')
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    new_handler = logging.StreamHandler()
    new_format = '%(asctime)s [%(name)s] [%(levelname)s] %(message)s'  # set your own formatting
    new_handler.setFormatter(logging.Formatter(new_format))
    logger.addHandler(new_handler)
    logger.setLevel(logging.INFO)  # switch to DEBUG for troubleshooting
    logger.propagate = False

    return logger


def lambda_handler(event, context):
    logger = setup_logging()  # for using our own log formatting

    stream = json.dumps(event['awslogs']['data'])

    # streaming log data is base64 encoded
    decode_stream = base64.b64decode(stream)

    # decompress the gzipped log stream
    stream_buffer = BytesIO(decode_stream)
    with gzip.GzipFile(mode='rb', fileobj=stream_buffer) as sb:
        data = sb.read()

    # convert from bytes to string
    string_data = data.decode('utf-8')
    logger.debug("String data:\n{}".format(string_data))

    # create a dict object. we'll add an interface value to the metrics
    json_metrics = json.loads(string_data)
    rds_fqdn = ''
    rds_log_id = json_metrics['logStream']
    logger.info("Got a metric stream from DB resource id: {}".format(rds_log_id))

    # let's see which rds these metrics are from
    rds_instances = rds_client.describe_db_instances()
    logger.debug("All RDS Instances: {}".format(rds_instances))

    for rds_instance in rds_instances['DBInstances']:
        if rds_instance['DbiResourceId'] == rds_log_id:
            rds_fqdn = rds_instance['Endpoint']['Address']
            logger.info("DB resource id belongs to {}".format(rds_fqdn))

    dns_resolver = dns.Resolver()
    answers = dns_resolver.query(rds_fqdn, 'A')
    for rdata in answers:
        logger.info("RDS hostname {} resolves to {}".format(rds_fqdn, rdata))

        # add ip address to metrics dict (there should only be one ip, so we add direct but if more a list is required.)
        json_metrics['ipAddress'] = str(rdata)
        logger.info("Updating RDS metrics with RDS IP Address")

    # dump dict object back to a json string
    string_payload = json.dumps(json_metrics)

    # use a bytearray for the mqtt publish
    b = bytearray(string_payload, 'utf-8')

    logger.info("Publishing to topic {} at the MQTT Endpoint {}".format(mqtt_topic, mqtt_endpoint))
    response = iot_client.publish(topic=mqtt_topic, qos=0, payload=b)
    logger.info("AWS IoT MQTT response status code: {}".format(response['ResponseMetadata']['HTTPStatusCode']))
