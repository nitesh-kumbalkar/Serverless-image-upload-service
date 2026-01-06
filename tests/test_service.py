import pytest
import json
import sys
import base64
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'resources'))
import service
from init_resources import create_resources

# Setup Fixture
@pytest.fixture(scope="module", autouse=True)
def setup_infrastructure():
    # Ensure resources exist before testing
    create_resources()

def test_upload_image():
    # Create dummy base64 image
    dummy_image = base64.b64encode(b"fake_image_bytes").decode('utf-8')
    
    event = {
        "body": json.dumps({
            "user_id": "user_123",
            "image_data": dummy_image,
            "category": "travel"
        })
    }
    
    response = service.upload_image(event, None)
    body = json.loads(response['body'])
    
    assert response['statusCode'] == 201
    assert body['data']['user_id'] == "user_123"
    assert "image_id" in body['data']

def test_list_images_filter_by_user():
    event = {
        "queryStringParameters": {
            "user_id": "user_123"
        }
    }
    response = service.list_images(event, None)
    body = json.loads(response['body'])
    
    assert response['statusCode'] == 200
    assert len(body['images']) > 0
    assert body['images'][0]['category'] == "travel"

def test_get_image_presigned_url():
    # 1. First get the image ID from the list
    list_event = {"queryStringParameters": {"user_id": "user_123"}}
    list_resp = service.list_images(list_event, None)
    image_id = json.loads(list_resp['body'])['images'][0]['image_id']

    # 2. Request download URL
    event = {
        "queryStringParameters": {
            "user_id": "user_123",
            "image_id": image_id
        }
    }
    response = service.get_image(event, None)
    body = json.loads(response['body'])
    
    assert response['statusCode'] == 200
    assert "download_url" in body
    assert "localhost:4566" in body['download_url'] # Verifies it points to LocalStack

def test_delete_image():
    # 1. Get image ID
    list_event = {"queryStringParameters": {"user_id": "user_123"}}
    list_resp = service.list_images(list_event, None)
    image_id = json.loads(list_resp['body'])['images'][0]['image_id']

    # 2. Delete
    event = {
        "body": json.dumps({
            "user_id": "user_123",
            "image_id": image_id
        })
    }
    response = service.delete_image(event, None)
    
    assert response['statusCode'] == 200
    assert json.loads(response['body'])['message'] == "Image deleted successfully"

if __name__ == "__main__":
    pytest.main([__file__])
    test_get_image_presigned_url()