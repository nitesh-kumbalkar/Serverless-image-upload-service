import boto3

# LocalStack configuration
ENDPOINT_URL = "http://localhost:4566"
AWS_REGION = "us-east-1"

def create_resources():
    # 1. Create S3 Bucket
    s3 = boto3.client('s3', endpoint_url=ENDPOINT_URL, region_name=AWS_REGION)
    bucket_name = "instagram-images-local"
    try:
        s3.create_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' created.")
    except Exception as e:
        print(f"Bucket might already exist: {e}")

    # 2. Create DynamoDB Table
    dynamodb = boto3.resource('dynamodb', endpoint_url=ENDPOINT_URL, region_name=AWS_REGION)
    table_name = "InstagramMetadata"
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},  # Partition Key
                {'AttributeName': 'image_id', 'KeyType': 'RANGE'} # Sort Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'image_id', 'AttributeType': 'S'},
                {'AttributeName': 'category', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'CategoryIndex',
                    'KeySchema': [
                        {'AttributeName': 'category', 'KeyType': 'HASH'},
                        {'AttributeName': 'user_id', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                     'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"✅ Table '{table_name}' created.")
    except Exception as e:
        print(f"Table might already exist: {e}")

if __name__ == '__main__':
    create_resources()