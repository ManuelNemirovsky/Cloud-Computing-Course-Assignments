import json
import os
import time
from typing import Any
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_dynamodb_client():
    return boto3.client('dynamodb')


def calculate_fee(arrival_time: str, current_time: str) -> tuple[float, float]:
    # Calculate total minutes
    total_minutes = (float(current_time) - float(arrival_time)) / 60
    rounded_minutes = ((total_minutes + 14) // 15) * 15
    parked_hours = rounded_minutes / 60
    fee = parked_hours * 10.0  # $10 per hour
    
    return parked_hours, fee


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        query_params = event.get('queryStringParameters', {})
        ticket_id = query_params.get('ticketId')
        
        logger.info(f"Received ticket_id: {ticket_id}")
        
        if not ticket_id:
            error_msg = 'Missing required parameter: ticketId'
            logger.error(error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': error_msg})
            }
        
        current_time = str(time.time())
        
        dynamodb = create_dynamodb_client()
        table_name = os.environ['DYNAMODB_TABLE_NAME']
        
        logger.info(f"Querying DynamoDB table: {table_name}")
        
        try:
            response = dynamodb.get_item(
                TableName=table_name,
                Key={
                    'PK': {'S': ticket_id}
                }
            )
            logger.info(f"DynamoDB response: {response}")
        except Exception as e:
            logger.error(f"Error querying DynamoDB: {str(e)}")
            raise
        
        if 'Item' not in response:
            error_msg = f'Ticket not found: {ticket_id}'
            logger.error(error_msg)
            return {
                'statusCode': 404,
                'body': json.dumps({'error': error_msg})
            }
        
        item = response['Item']
        logger.info(f"Found item: {item}")
        
        arrival_time = item['arrival_time']['S']
        license_plate = item['entry_plate']['S']
        parking_lot = item['parking_lot']['S']
        is_still_there = item.get('is_still_there', {}).get('BOOL', True)
        
        if not is_still_there:
            error_msg = 'Vehicle has already exited'
            logger.error(error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': error_msg})
            }
        
        parked_time, fee = calculate_fee(arrival_time, current_time)
        logger.info(f"Calculated fee: {fee}, parked time: {parked_time}")
        
        try:
            dynamodb.update_item(
                TableName=table_name,
                Key={
                    'PK': {'S': ticket_id}
                },
                UpdateExpression='SET is_still_there = :false, exit_time = :exit_time, fee = :fee',
                ExpressionAttributeValues={
                    ':false': {'BOOL': False},
                    ':exit_time': {'S': current_time},
                    ':fee': {'S': str(fee)}
                }
            )
            logger.info("Successfully updated record")
        except Exception as e:
            logger.error(f"Error updating record: {str(e)}")
            raise
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'licensePlate': license_plate,
                'parkedTime': round(parked_time, 2),
                'parkingLot': parking_lot,
                'charge': round(fee, 2)
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        } 