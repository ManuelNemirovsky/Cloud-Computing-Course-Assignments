# Cloud Computing Course Assignments

This repository contains the assignments and exercises completed during `Cloud Computing course`


## Repository Structure
Each folder in this repository represents a different exercise or assignment from the course:

### Exercise 1: Serverless Parking Lot Management System
A serverless application that manages a parking lot system using:
- AWS Lambda for serverless functions
- DynamoDB for data storage
- API Gateway for REST API endpoints
- Pulumi for Infrastructure as Code

The system handles:
- Vehicle entry registration
- Parking Lot occupancy tracking
- Vehicle exit processing

#### API Response Examples

##### Valid Entry Response
When a vehicle successfully enters the parking lot, the API returns a ticket ID and success message:
```
{
    "ticketId": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Entry recorded successfully"
}
```

[Insert your valid entry response picture here]
*Figure 1: Example of a successful vehicle entry response*

##### Valid Exit Response
When a vehicle successfully exits the parking lot, the API returns the parking duration and fee:
```
{
    "duration": "2 hours",
    "fee": 10.00,
    "message": "Exit processed successfully"
}
```

[Insert your valid exit response picture here]
*Figure 2: Example of a successful vehicle exit response*

## Technologies Used
- `Python`
- `AWS Services` (Lambda, DynamoDB, API Gateway)
- `Pulumi` (Infrastructure as Code)
- `REST APIs`
- `Serverless` Architecture

## Getting Started
Each exercise folder contains its own README with specific setup and deployment instructions.