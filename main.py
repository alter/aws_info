#!/usr/bin/env python2
import boto3
from lxml import etree
import urllib2
import json
import sys

site_with_price = 'https://www.ec2instances.info'

AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''

regions_map = {'us-east-1': 'N.Virginia',
               'us-east-2': 'Ohio',
               'us-west-1': 'N.California',
               'us-west-2': 'Oregon',
               'ca-central-1': 'Canada',
               'eu-west-1': 'Ireland',
               'eu-central-1': 'Frankfurt',
               'eu-west-2': 'London',
               'ap-southeast-1': 'Singapore',
               'ap-southeast-2': 'Sydney',
               'ap-northeast-2': 'Seoul',
               'ap-northeast-1': 'Tokyo',
               'ap-south-1': 'Mumbai',
               'sa-east-1': 'Sao Paulo'}



def get_instance_price(region, instance_type):
    response = urllib2.urlopen(site_with_price)
    html = response.read()

    table= etree.HTML(html).find("body/table/tbody")
    rows = iter(table)
    for row in rows:
        if row.attrib['class'] == 'instance':
            if row.attrib['id'] == instance_type:
                for col in row:
                    if 'data-pricing' in col.attrib:
                        price = col.attrib['data-pricing']
                        break

    price_json = json.loads(price)
    return price_json[region]

try:
    f = open('aws_info.csv', 'w')
    f.write("Region,Instance ID,Name,Instance type,USD/hour,USD/31days,State,Public IP,Key name,EBS Optimized,Volume sizes(GB)\n")

    for region in regions_map.iterkeys():
        if region != 'us-west-1':
            continue
        client = boto3.client('ec2',
                              aws_access_key_id=AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                              region_name=region)
        response = client.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                print instance
                sys.exit(1)
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        name_tag = tag['Value']
                state = instance['State']['Name']
                ebsoptimized = instance['EbsOptimized']
                public_ip = instance['PublicIpAddress']
                instance_id = instance['InstanceId']
                key_name = instance['KeyName']
                instance_az = instance['Placement']['AvailabilityZone']
                instance_type = instance['InstanceType']
                instance_price = get_instance_price(region, instance_type)
                instance_price_per_month = float(instance_price) * 24 * 31
                ec2 = boto3.resource('ec2', region_name=region)
                ec2_instance = ec2.Instance(instance['InstanceId'])
                volumes = ec2_instance.volumes.all()
                instance_volume_sizes = []
                for v in volumes:
                    instance_volume_sizes.append(v.size)
                f.write("{},{},{},{},{},{},{},{},{},{},{},{}\n".format(regions_map[region], instance_id, name_tag,
                                                                 instance_type, instance_az, instance_price,
                                                                 instance_price_per_month, state, public_ip, key_name,
                                                                 ebsoptimized, str(instance_volume_sizes)))
except IOError as e:
    print "I/O error({0}): {1}".format(e.errno, e.strerror)
except ValueError:
    print "Could not convert data to an integer."
except:
    print "Unexpected error:", sys.exc_info()[0]
    raise
finally:
    f.close()
