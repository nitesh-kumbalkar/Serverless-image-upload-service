# Serverless Image Upload Service

A scalable, serverless backend service for an Instagram-like application. This module handles image uploads, storage, and metadata management using Python, AWS Lambda, S3, and DynamoDB.

The development environment is fully containerized using LocalStack to emulate AWS services locally.

## Architecture
Language: Python 3.7+

Compute: AWS Lambda (Stateless execution)

Object Storage: Amazon S3 (Stores binary image files)

Database: Amazon DynamoDB (Stores metadata: User ID, Tags, Timestamps)

Local Emulation: LocalStack (Docker)

## Project Structure

.
├── docker-compose.yml    # Configuration for LocalStack (S3, DynamoDB, Lambda)
├── resources/init_resources.py     # Initialize S3 Bucket and DynamoDB Table
├── src/service.py            # Main Application Logic (Lambda Handlers)
├── tests/test_service.py       # Integration Tests (Pytest)
├── requirements.txt      # Python dependencies
└── README.md             # Project Documentation

## Getting Started
Prerequisites
Python 3.7+

Docker & Docker Compose

pip (Python Package Manager)

1. Environment Setup
Clone the repository and create a virtual environment:

Bash

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
2. Install Dependencies
Bash

pip install boto3 pytest
3. Start Local Infrastructure
Start LocalStack to emulate AWS services on your machine. This runs on port 4566.

Bash

docker-compose up -d
4. Initialize Resources
Run the initialization script to create the S3 Bucket (instagram-images-local) and the DynamoDB Table (InstagramMetadata).

Bash

python resources/init_resources.py
Expected Output:

Plaintext

✅ Bucket 'instagram-images-local' created.
✅ Table 'InstagramMetadata' created.
🧪 Running Tests
The project uses pytest for integration testing. These tests interact with the running LocalStack container to simulate real-world API calls, storage, and database queries.

Bash

pytest tests/test_service.py -v
📡 API Documentation
Since this is a Lambda-based service, the functions in service.py act as handlers. Below are the contracts for the API endpoints.

1. Upload Image
Function: upload_image

Input: JSON Body with Base64 encoded image string.

Storage: Saves file to S3, metadata to DynamoDB.

Request Body:

JSON

{
  "user_id": "john_doe",
  "image_data": "<base64_string>",
  "category": "travel"
}
2. List Images
Function: list_images

Input: Query Parameters.

Behavior: Supports filtering by user or category.

Query Parameters:

user_id (Optional): Filter by user.

category (Optional): Filter by tag/category.

3. View/Download Image
Function: get_image

Input: Query Parameters (user_id, image_id).

Behavior: Returns a Presigned URL allowing direct, secure access to S3 for a limited time.

Response:

JSON

{
  "download_url": "http://localhost:4566/...",
  "metadata": { ... }
}
4. Delete Image
Function: delete_image

Input: JSON Body.

Behavior: Removes the file from S3 and the entry from DynamoDB.

Request Body:

JSON

{
  "user_id": "john_doe",
  "image_id": "unique-uuid-123"
}
⚙️ scalability Design Notes
DynamoDB Schema: Uses user_id as the Partition Key for efficient user lookups. A Global Secondary Index (GSI) is used for querying by category.

S3 Offloading: The API does not serve binary files. It generates Presigned URLs, offloading the bandwidth load to S3.

Stateless: The Lambda functions contain no local state, allowing infinite horizontal scaling.

Troubleshooting
Error: Connection refused

Ensure Docker is running.

Ensure LocalStack is up: docker ps should show the container running on port 4566.

Error: ResourceNotFoundException

You likely forgot to run python init_resources.py after restarting Docker. LocalStack data is ephemeral unless volume mapping is persistent.
