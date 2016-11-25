import json
import boto3
from boto3.session import Session

import time
from datetime import datetime as dt

def lambda_handler(event, context):
    ec2_client   = boto3.client('ec2')
    as_client   = boto3.client('autoscaling')

    # get the latest backup of AMI.
    image_id = get_latests_image_id(ec2_client)

    # get all Launch Configurations.
    configs = get_launch_configs(as_client)

    # create new Launch Configuration.
    launch_config_name = create_launch_config(as_client, image_id)

    # update the Auto Scaling group setting.
    update_auto_scaling_group(as_client, launch_config_name)
    
    if (configs is not None):
        delete_old_launc_config(as_client, configs)
        
    return 0

def get_latests_image_id(ec2_client):
    sorted_images = get_sorted_images(ec2_client)
    return sorted_images[0]['ImageId']
    
def get_sorted_images(ec2_client):
    sorted_images = []

    response = ec2_client.describe_images(
        Owners  = ['self'],
        Filters = [
            {
                'Name': 'tag:Name',
                'Values': ['example.com']
            }
        ]
    )

    images = response['Images']
    sorted_images = sorted(
        images, 
        key = lambda x: x['CreationDate'], 
        reverse = True
    )

    return sorted_images
    
def get_launch_configs(as_client):
    response = as_client.describe_launch_configurations()
    
    configs = []
    
    if response is not None:
        for config in response['LaunchConfigurations']:
            launch_configuration = config['LaunchConfigurationName']
            
            if ('example.com' in launch_configuration):
                configs.append(launch_configuration)
            
    return configs
    
def create_launch_config(as_client, image_id):
    launch_configuration_name = 'example.com_' + dt.now().strftime('%Y%m%d%H%M%S')

    response = as_client.create_launch_configuration(
        LaunchConfigurationName = launch_configuration_name,
        ImageId = image_id,
        KeyName = 'your keypair',
        SecurityGroups = ['your security group name'],
        InstanceType = 't2.micro',
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'VolumeSize': 8,
                    'VolumeType': 'gp2',
                    'DeleteOnTermination': True
                }
            }
        ]
    )
    
    return launch_configuration_name

def delete_old_launc_config(as_client, configs):
    for config in configs:
        response = as_client.delete_launch_configuration(
            LaunchConfigurationName = config
        )
    
    return True
    
def update_auto_scaling_group(as_client, launch_configuration_name):
    as_client.update_auto_scaling_group(
        AutoScalingGroupName = 'your auto scaling group name',
        LaunchConfigurationName = launch_configuration_name
    )
    
    return True
