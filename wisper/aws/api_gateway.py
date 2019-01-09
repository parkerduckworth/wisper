import json
import requests

from werkzeug.exceptions import BadGateway


def lambda_proxy(action):
    """Invoke Lambda function through API Gateway to start/stop EC2 server
         instance

       action: (str) Only valid arguments are 'start_instance' and
         'stop_instance'.

    """

    if action != 'start_instance' and action != 'stop_instance':
        raise ValueError('Invalid argument for ec2_handler: %s' % action)

    # Input to the Lambda function
    payload = {'action': action}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(
        # API Gateway endpoint
        'https://mvht1yr1c8.execute-api.us-east-2.amazonaws.com/prod/{proxy+}',
         data=json.dumps(payload), headers=headers)
    # API Gateway max timeout is very close to EC2 instance startup time.
    if action == 'start_instance' and response.status_code == 504:
        # Try again
        return lambda_proxy(action)

    # Instance state == 'stopping'
    if response.status_code == 502:
        raise BadGateway('Server is shutting down. Try again in a minute.')

    return response.json()['public_ip_address']
