import boto3
import os

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.environ.get('AWS_REGION', 'us-west-2')
)

table = dynamodb.create_table(
    TableName='EddieBusBookings',
    KeySchema=[
        {'AttributeName': 'ticket_id', 'KeyType': 'HASH'}
    ],
    AttributeDefinitions=[
        {'AttributeName': 'ticket_id', 'AttributeType': 'S'}
    ],
    BillingMode='PAY_PER_REQUEST'
)

table.wait_until_exists()
print("Table created successfully:", table.table_name)