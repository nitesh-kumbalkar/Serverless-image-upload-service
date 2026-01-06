"""Pytest configuration and shared fixtures."""
import os
import pytest
import boto3
from moto import mock_dynamodb, mock_s3

# Set environment variables before importing app modules
os.environ["AWS_REGION"] = "us-east-1"
os.environ["S3_BUCKET"] = "images-bucket"
os.environ["DDB_TABLE"] = "images"


@pytest.fixture
def aws_credentials():
    """Fixture to set up AWS credentials for tests."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
@mock_s3
@mock_dynamodb
def aws_services(aws_credentials):
    """
    Fixture to set up mocked AWS services (S3 and DynamoDB).
    
    Yields after creating S3 bucket and DynamoDB table.
    """
    # Create S3 bucket
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="images-bucket")

    # Create DynamoDB table
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName="images",
        KeySchema=[{"AttributeName": "image_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "image_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "user_id-index",
                "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            }
        ],
        BillingMode="PROVISIONED",
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )

    yield

    # Teardown handled automatically by moto


def _build_multipart_body(
    fields_dict,
    file_bytes,
    boundary="----WebKitFormBoundary7MA4YWxkTrZu0gW",
):
    """Build a multipart/form-data body."""
    parts = []

    # Add text fields
    for name, value in fields_dict.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        )

    # Add file field
    if file_bytes:
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        )

    body = "".join(parts).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()

    return body, boundary


@pytest.fixture
def multipart_builder():
    """Fixture to provide multipart body builder."""
    return _build_multipart_body
