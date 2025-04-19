import uuid
import os
import time
import datetime
from typing import Any
import boto3
import logging
from http import HTTPStatus
from utils.response_utils import create_response, create_error_response
from utils.field_names import FieldNames

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_dynamodb_client():
    return boto3.client('dynamodb')


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        query_params = event.get('queryStringParameters', {})
        license_plate = query_params.get(FieldNames.PLATE.value)
        parking_lot_id = query_params.get(FieldNames.PARKING_LOT.value)
        
        logger.info(f"Received request - License Plate: {license_plate}, "
                    "Parking Lot: {parking_lot_id}")
        
        if not license_plate or not parking_lot_id:
            error_msg = "Missing required parameters: plate and parkingLot are required"
            logger.error(error_msg)
            return create_error_response(HTTPStatus.BAD_REQUEST, error_msg)
        
        dynamodb = create_dynamodb_client()
        table_name = os.environ['DYNAMODB_TABLE_NAME']
        
        try:
            scan_response = dynamodb.scan(
                TableName=table_name,
                FilterExpression=f'{FieldNames.ENTRY_PLATE.value} = :plate AND '
                               f'{FieldNames.IS_STILL_THERE.value} = :true',
                ExpressionAttributeValues={
                    ':plate': {FieldNames.STRING.value: license_plate},
                    ':true': {FieldNames.BOOLEAN.value: True}
                }
            )
            
            if scan_response.get('Items'):
                error_msg = f'Vehicle with license plate {license_plate} is already in the parking lot'
                logger.error(error_msg)
                return create_error_response(HTTPStatus.BAD_REQUEST, error_msg)
        except Exception as e:
            logger.error(f"Error checking for existing vehicle: {str(e)}")
            return create_error_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                'Failed to check vehicle status'
            )
        
        try:
            scan_response = dynamodb.scan(
                TableName=table_name,
                FilterExpression=f'{FieldNames.PARKING_LOT_ID.value} = :lot AND '
                               f'{FieldNames.IS_STILL_THERE.value} = :true',
                ExpressionAttributeValues={
                    ':lot': {FieldNames.STRING.value: parking_lot_id},
                    ':true': {FieldNames.BOOLEAN.value: True}
                }
            )
            
            if scan_response.get('Items'):
                error_msg = f'Parking lot {parking_lot_id} is already occupied'
                logger.error(error_msg)
                return create_error_response(HTTPStatus.BAD_REQUEST, error_msg)
        except Exception as e:
            logger.error(f"Error checking parking lot status: {str(e)}")
            return create_error_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                'Failed to check parking lot status'
            )
        
        customer_id = str(uuid.uuid4())
        ticket_id = str(uuid.uuid4())
        current_time = str(time.time())
        
        try:
            dynamodb.put_item(
                TableName=table_name,
                Item={
                    FieldNames.PK.value: {FieldNames.STRING.value: ticket_id},
                    FieldNames.CUSTOMER_ID.value: {FieldNames.STRING.value: customer_id},
                    FieldNames.ENTRY_PLATE.value: {FieldNames.STRING.value: license_plate},
                    FieldNames.PARKING_LOT_ID.value: {FieldNames.STRING.value: parking_lot_id},
                    FieldNames.CREATED_AT.value: {FieldNames.STRING.value: datetime.datetime.now().isoformat()},
                    FieldNames.ARRIVAL_TIME.value: {FieldNames.STRING.value: current_time},
                    FieldNames.IS_STILL_THERE.value: {FieldNames.BOOLEAN.value: True}
                }
            )
            logger.info(f"Successfully stored entry for ticket {ticket_id}")
        except Exception as e:
            logger.error(f"Error storing entry in DynamoDB: {str(e)}")
            return create_error_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                'Failed to store entry'
            )
        
        return create_response(
            HTTPStatus.OK,
            {
                FieldNames.TICKET_ID.value: ticket_id,
                FieldNames.MESSAGE.value: 'Entry recorded successfully'
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_error_response(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            'Internal server error'
        )