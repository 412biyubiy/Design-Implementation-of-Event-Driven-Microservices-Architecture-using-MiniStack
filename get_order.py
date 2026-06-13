# get_order.py
import json
import boto3
import os
import decimal

endpoint_url = os.environ.get('AWS_ENDPOINT_URL') or "http://localhost:4566"
dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
table = dynamodb.Table('Orders')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 == 0:
                return int(o)
            return float(o)
        return super(DecimalEncoder, self)

def lambda_handler(event, context):
    order_id = event.get('orderId') or event.get('pathParameters', {}).get('id')
    
    if not order_id:
        return {"statusCode": 400, "body": json.dumps({"error": "Missing orderId"})}
        
    response = table.get_item(Key={'orderId': order_id})
    item = response.get('Item')
    
    if not item:
        return {"statusCode": 404, "body": json.dumps({"error": "Order not found"})}
        
    return {
        "statusCode": 200,
        "body": json.dumps(item, cls=DecimalEncoder)
    }