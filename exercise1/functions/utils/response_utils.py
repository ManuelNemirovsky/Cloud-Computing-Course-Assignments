import json
from typing import Any
from http import HTTPStatus


def create_response(
    status_code: HTTPStatus,
    body: dict[str, Any],
    headers: dict[str, str] = None
) -> dict[str, Any]:
    response = {
        'statusCode': status_code.value,
        'body': json.dumps(body),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        }
    }
    if headers:
        response['headers'].update(headers)    
    return response


def create_error_response(
    status_code: HTTPStatus,
    error_message: str
) -> dict[str, Any]:
    return create_response(
        status_code=status_code,
        body={'error': error_message}
    )
