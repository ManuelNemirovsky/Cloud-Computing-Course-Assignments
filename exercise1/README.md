# Cloud Computing Course | Reichman University (#3031)

| Student Name | Student ID |
|-------------|------------|
| Manuel Nemirovsky | 211338108 |
| Gilad Amir | 211338108 |

# Parking Lot Management System

A serverless parking lot management system built with AWS Lambda, API Gateway, and DynamoDB. This system allows for vehicle entry and exit management with automated fee calculation.

## Features

### Entry Management
- Vehicle entry registration with license plate and parking lot assignment
- Prevention of duplicate entries for the same license plate
- Prevention of multiple vehicles in the same parking lot
- Unique ticket generation for each entry
- Real-time parking lot occupancy tracking

### Exit Management
- Vehicle exit processing with ticket validation
- Automated parking fee calculation ($10 per hour, rounded up to nearest 15 minutes)
- Prevention of ticket reuse
- Real-time parking lot status updates

### Security & Validation
- Input validation for all operations
- Protection against duplicate entries
- Protection against parking lot over-occupancy
- Protection against ticket reuse
- Comprehensive error handling and logging

## Architecture

The system is built using:
- **AWS Lambda**: Serverless compute for entry and exit functions
- **API Gateway**: REST API endpoints for entry and exit operations
- **DynamoDB**: NoSQL database for storing parking records
- **Pulumi**: Infrastructure as Code (IaC) for AWS resource management
- **Python**: Backend implementation language

## Prerequisites

1. **AWS Account**
   - Active AWS account with appropriate permissions
   - AWS CLI configured with credentials

2. **Development Tools**
   - Python 3.8 or higher
   - pip (Python package manager)
   - Pulumi CLI
   - AWS SAM CLI (optional, for local testing)

3. **Dependencies**
   - boto3 (AWS SDK for Python)
   - Pulumi AWS provider
   - Python standard libraries (json, uuid, datetime, etc.)

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/ManuelNemirovsky/Cloud-Computing-Course-Assignments
   cd exercise1
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure AWS Credentials**
   ```bash
   aws configure
   ```
   Enter your AWS access key ID, secret access key, default region, and output format.

5. **Configure Pulumi**
   ```bash
   pulumi login
   pulumi stack init dev
   ```

## Deployment

1. **Deploy Infrastructure**
   ```bash
   cd pulumi
   pulumi up
   ```
   This will create:
   - `DynamoDB` table
   - `Lambda` functions
   - `API Gateway` endpoints
   - `IAM roles` and `policies`

2. **Environment Variables**
   After deployment, set the following environment variables:
   - `DYNAMODB_TABLE_NAME`: Name of the DynamoDB table (self generated with suffix)
   - `AWS_REGION`: AWS region where resources are deployed (self generated with suffix)

## API Endpoints

### Entry Endpoint
```
POST /entry
Query Parameters:
- plate: Vehicle license plate number
- parkingLot: Parking lot identifier

Response:
{
    "ticketId": "unique-ticket-id",
    "message": "Entry recorded successfully"
}
```

### Exit Endpoint
```
POST /exit
Query Parameters:
- ticketId: Unique ticket identifier

Response:
{
    "licensePlate": "ABC123",
    "parkedTime": 2.5,
    "parkingLot": "A1",
    "charge": 25.0
}
```

## Error Handling

The system returns appropriate HTTP status codes and error messages:

- 400: Bad Request (invalid input, duplicate entry, etc.)
- 404: Not Found (invalid ticket)
- 500: Internal Server Error

## Monitoring Tools We Used

- `CloudWatch` Logs for Lambda functions
- `API Gateway` metrics for endpoint usage