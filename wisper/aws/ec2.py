"""This module runs in AWS Lambda"""

import boto3
import json
import os

from botocore.exceptions import ClientError


INSTANCE_ID = os.environ['INSTANCE_ID']


def lambda_handler(event, context):
    """Entry point into the Lambda function

       event: (Lambda event object) contains the payload from the client
         invocation
    """

    body = json.loads(event['body'])

    response = {}
    if body['action'] == 'start_instance':
        host = start_ec2_instance()
        response['body'] = json.dumps(
            {'public_ip_address': host, 'state': 'started'})
    else:
        stop_ec2_instance()
        response['body'] = json.dumps(
            {'public_ip_address': None, 'state': 'shutdown'})
    response['statusCode'] = 200
    return response


ec2 = boto3.client('ec2')


def start_ec2_instance():
    if check_instance_state():
        # Returns True if running
        return get_public_ip()
    # Do a dryrun first to verify permissions
    try:
        ec2.start_instances(InstanceIds=[INSTANCE_ID], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise
    # Dry run succeeded, start the instance
    try:
        ec2.start_instances(InstanceIds=[INSTANCE_ID], DryRun=False)
        print 'Waiting for EC2 instance to start...'
        ec2.get_waiter('image_available').wait()
        print 'Instance started'
        run_wisper_server()
        print 'Remote server running'
        return get_public_ip()
    except ClientError, e:
        print e


def stop_ec2_instance():
    # Do a dryrun first to verify permissions
    try:
        ec2.stop_instances(InstanceIds=[INSTANCE_ID], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise
    # Dry run succeeded, call stop_instances without dryrun
    try:
        ec2.stop_instances(InstanceIds=[INSTANCE_ID], DryRun=False)
        print 'Shutting down EC2 instance'
        return
    except ClientError as e:
        print e


def check_instance_state():
    """Determine current state of instance"""

    res = boto3.resource('ec2')
    state = res.Instance(INSTANCE_ID).state[u'Name']
    if state == 'stopping':
        raise RuntimeError('The instance is stopping and cannot be started.')
    return state == 'running'


def run_wisper_server():
    """Run the shell command to start a wisper server instance"""

    try:
        print 'Starting wisper server'
        ssm_client = boto3.client('ssm')
        resp = ssm_client.send_command(
            DocumentName='AWS-RunShellScript',
            Parameters={'commands': ['wisper-runserver']},
            InstanceIds=[INSTANCE_ID])
        return resp
    except:
        stop_ec2_instance()
        raise RuntimeError('Wisper server unable to run')


def get_public_ip():
    """Retrieve public IP address of most recently launched instance"""

    try:
        running_instances = []
        response = ec2.describe_instances()
        # Collect running instances
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if instance[u'State'][u'Name'] == 'running':
                    running_instances.append(instance)
        # Select instance with newest launch time
        most_recent_instance = min(running_instances, key=lambda x: x[u'LaunchTime'])
        return most_recent_instance[u'PublicIpAddress']
    except ValueError:
        print 'EC2 instance not running'
