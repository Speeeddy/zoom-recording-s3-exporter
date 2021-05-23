import json
import os
import requests
import boto3
import pprint

client = boto3.client('s3')
bucket = os.environ["BucketName"]

def lambda_handler(sqsEvent, context):
    print(sqsEvent)
    event = json.loads(sqsEvent['Records'][0]['body'])  # Handling only one event at a time, limited by SQS batch size in Lambda triggers
    print(f"Received event from Zoom - {event['event']} for meeting {event['payload']['object'].get('topic')}")

    meetingName = event['payload']['object'].get('topic') or str(event['payload']['object'].get('id'))
        
    for recordingEvent in event['payload']['object']['recording_files']:
        if 'file_size' in recordingEvent and recordingEvent['file_size'] > 500000:
            print("Filesize is greater than 500 MB, skipping")
            continue
        downloadUrl = recordingEvent['download_url']
        
        filePath = "/tmp/"
        fileName = recordingEvent['recording_type'] if 'recording_type' in recordingEvent else "Unnamed"
        extension = f".{recordingEvent['file_type']}" if 'file_type' in recordingEvent else ''
        localFilename = fileName + extension 
        fileUri = filePath + localFilename

        getHeaders = {'Accept': 'application/json'}
        if 'download_token' in event:
            getHeaders['Authorization'] = f"Bearer: {event['download_token']}"
            
        with requests.get(downloadUrl, stream=True, headers=getHeaders) as r:
            r.raise_for_status()
            with open(fileUri, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
        
        with open(fileUri, 'rb') as f:
            s3Response = client.put_object(
                Body=f,
                Bucket=bucket,
                Key=f"{meetingName}/{localFilename}"
            )
    return 