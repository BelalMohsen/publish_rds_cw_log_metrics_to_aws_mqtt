# publish_rds_cw_log_metrics_to_aws_mqtt
==========

*Rev 0.1*

A team from enet, OpenNMS and Arista worked together on streaming data at the RIPE NCC & iNOG Hackaton18 in Dublin
This code was for getting metrics from AWS instances and publishing them for OpenNMS to ingest.

**This Lambda Function should:**
- Receive Cloudwatch log streaming events from the RDSOSMetrics LogGroup
- Determine the Source RDS
- Get the RDS IP Address
- Add it to the log metrics
- Publish it to an AWS IoT MQTT topic

**Ancillary Dependencies**
- Cloudwatch Enhanced Monitoring configured on RDS
- RDSOSMetrics LogGroup streamed to a Lamba Function
- IoT Thing Device configured to create an MQTT Broker

Our specific usecase was to stream enhanced monitoring logs for RDS instances to an MQTT Broker and have the MQTT Client of OpenNMS ingest them into The NEWTS Cassandra Time Series DB for futher analysis and visualisation. Any MQTT Client should be able to subscribe to and use this data in a multitude of ways.
The Metrics are in an easy to parse JSON format.

