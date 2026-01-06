import json
import boto3
import uuid
import base64
import time
from botocore.exceptions import ClientError
from decimal import Decimal

# Configuration
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
BUCKET_NAME = "instagram-images-local"
TABLE_NAME = "InstagramMetadata"

# Initialize Clients
s3_client = boto3.client('s3', endpoint_url=ENDPOINT_URL, region_name=REGION)
dynamodb = boto3.resource('dynamodb', endpoint_url=ENDPOINT_URL, region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

def response(status, body):
    return {
        "statusCode": status,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"}
    }

def decimal_to_native(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    elif isinstance(obj, list):
        return [decimal_to_native(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    return obj

# 1. Upload Image
def upload_image(event, context):
    try:
        body = json.loads(event['body'])
        user_id = body.get('user_id')
        image_data = body.get('image_data') # Base64 string
        category = body.get('category', 'general')
        
        if not user_id or not image_data:
            return response(400, {"error": "Missing user_id or image_data"})

        image_id = str(uuid.uuid4())
        file_key = f"{user_id}/{image_id}.jpg"
        
        # Upload to S3
        image_binary = base64.b64decode(image_data)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=image_binary,
            ContentType='image/jpeg'
        )

        # Save Metadata to DynamoDB
        metadata = {
            'user_id': user_id,
            'image_id': image_id,
            'category': category,
            's3_key': file_key,
            'timestamp': int(time.time()),
            'file_size': len(image_binary)
        }
        table.put_item(Item=metadata)

        return response(201, {"message": "Upload successful", "data": metadata})

    except Exception as e:
        return response(500, {"error": str(e)})

# 2. List Images (Supports filters: user_id, category)
def list_images(event, context):
    params = event.get('queryStringParameters', {}) or {}
    user_id = params.get('user_id')
    category = params.get('category')

    try:
        if category:
            # Query GSI if filtering by category
            resp = table.query(
                IndexName='CategoryIndex',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('category').eq(category)
            )
        elif user_id:
            # Query Primary Key if filtering by user
            resp = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
            )
        else:
            # Scan (Expensive, but okay for listing all in small scale)
            resp = table.scan()

        return response(200, {"images": decimal_to_native(resp.get('Items', []))})
    except Exception as e:
        return response(500, {"error": str(e)})

# 3. View/Download Image
def get_image(event, context):
    # Generates a Presigned URL for secure, temporary access
    params = event.get('queryStringParameters', {})
    user_id = params.get('user_id')
    image_id = params.get('image_id')

    if not user_id or not image_id:
        return response(400, {"error": "Missing user_id or image_id"})

    try:
        # Check if exists in DB first
        resp = table.get_item(Key={'user_id': user_id, 'image_id': image_id})
        if 'Item' not in resp:
            return response(404, {"error": "Image not found"})

        file_key = resp['Item']['s3_key']
        
        # Generate Presigned URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': file_key},
            ExpiresIn=3600
        )
        return response(200, {"download_url": url, "metadata": decimal_to_native(resp['Item'])})
    except Exception as e:
        return response(500, {"error": str(e)})

# 4. Delete Image
def delete_image(event, context):
    body = json.loads(event['body'])
    user_id = body.get('user_id')
    image_id = body.get('image_id')

    if not user_id or not image_id:
        return response(400, {"error": "Missing user_id or image_id"})

    try:
        # Get Key to delete from S3
        resp = table.get_item(Key={'user_id': user_id, 'image_id': image_id})
        if 'Item' in resp:
            s3_key = resp['Item']['s3_key']
            
            # Delete from S3
            s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
            
            # Delete from DynamoDB
            table.delete_item(Key={'user_id': user_id, 'image_id': image_id})
            
            return response(200, {"message": "Image deleted successfully"})
        else:
            return response(404, {"error": "Image not found"})
            
    except Exception as e:
        return response(500, {"error": str(e)})