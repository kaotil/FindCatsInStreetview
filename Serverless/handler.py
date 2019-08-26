import requests
import datetime
import json
import os
import re
import random
import logging
import boto3
from boto3.session import Session

# log
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# settings
apikey = os.environ['GOOGLE_APIKEY']
upload_dir = 'img'
check_words = 'cat|dog|animal|pet'
move = 0.0002
roop = 4

# aws settings
session = Session()

# global settings
rekognition=session.client('rekognition')
bucket = boto3.resource('s3').Bucket(os.environ['S3_BACKET_NAME'])
logger.info(os.environ['S3_BACKET_NAME'])

def get_snapped_point(points_str):
    url = "https://roads.googleapis.com/v1/snapToRoads"
    req = requests.get(url, params={'key': apikey, 'path': points_str})

    return req.json()['snappedPoints']
            
def get_streetview_image(latitude, longitude, heading):
    url = 'https://maps.googleapis.com/maps/api/streetview'

    params = {'key': apikey,
                'size': '600x600',
                'location': '%s,%s' % (latitude, longitude),
                'heading': heading,
                'fov': '90',
                'pitch': '10'}
                
    req = requests.get(url, params=params)

    return req.content
    
def run_rekognition(content):
    labels = []
    response = rekognition.detect_labels(Image={'Bytes': content})

    for label in response['Labels']:
        #logger.info(label['Name'] + ' : ' + str(label['Confidence']))
        if re.match(check_words, label['Name'], re.IGNORECASE):
            labels.append([label['Name'], label['Confidence']])

    return labels

def upload_image_s3(content, filepath):
    bucket.put_object(Body=content, Key=filepath, ACL='public-read', ContentType="image/jpeg")

def is_latitude(value):
    # 緯度 -90 ～ 90
    rep = '^(\\+|-)?(?:90(?:(?:\\.0{1,15})?)|(?:[0-9]|[1-8][0-9])(?:(?:\\.[0-9]{1,15})?))$'
    return re.match(rep, value) != None;
    
def is_longitude(value):
    # 経度 -180 ～ 180
    rep = '^(\\+|-)?(?:180(?:(?:\\.0{1,15})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])(?:(?:\\.[0-9]{1,15})?))$'
    return re.match(rep, value) != None;
    
def index(event, context):
    logger.info('- - - - - START - - - - -')
    logger.info('location: %s' % (event['location']))
    
    data = []

    try:
        (s_latitude, s_longitude) = event['location'].split(',')
        if (not is_latitude(s_latitude) or not is_longitude(s_longitude)):
            raise Exception('location is invalid. (%s)' % (event['location']))
            
        s_latitude = float(s_latitude)
        s_longitude = float(s_longitude)
        
        # Get location
        latitudes = [s_latitude + (i * move) for i in range(roop)]
        for i in range(roop):
            longitudes = [s_longitude + (i * move) for j in range(roop)]
            points = ["%s,%s" % (latitudes[i], longitudes[i]) for i in range(roop)]
            snapped_points = get_snapped_point('|'.join(points))
            
            for j in snapped_points:
                logger.info('%s: %s,%s' % (j['originalIndex'], j['location']['latitude'], j['location']['longitude']))
                data.append({'point': '%s,%s' % (j['location']['latitude'], j['location']['longitude']), 'line_no': i})
                
                for heading in [0, 90, 180, 270]:
                    # Get image
                    content = get_streetview_image(j['location']['latitude'], j['location']['longitude'], heading)
                    
                    # Run Rekognition
                    labels = run_rekognition(content)
                    if len(labels):
                        logger.info(labels)
                        filepath = '%s/%s_%s_%s.jpg' % (upload_dir, j['location']['latitude'], j['location']['longitude'], heading)
                        data[len(data)-1]['matches'] = [{'heading': heading, 'filepath': filepath, 'labels':labels}]
                        
                        # Upload images
                        upload_image_s3(content, filepath)
                        
    except Exception as e:
        raise Exception("{'Error: ': %s}" % (e.args))

    logger.info(json.dumps(data))
    logger.info('- - - - - END - - - - -')
    return json.dumps(data)