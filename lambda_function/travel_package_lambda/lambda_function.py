import json
import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    city = event['city']
    print(f'city: {city}')
    client = boto3.client('dynamodb')

    try:
        response = client.get_item(
            TableName='travel_packages',
            Key={'city': {'S': city}}
        )
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    item = response.get('Item')
    if item is None:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': f'No travel package found for city: {city}'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps(item)
    }
