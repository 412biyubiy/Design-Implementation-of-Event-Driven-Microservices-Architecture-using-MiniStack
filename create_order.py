# create_order.py
import json
import uuid
import boto3
import os

# Menggunakan endpoint internal localstack jika tersedia
endpoint_url = os.environ.get('AWS_ENDPOINT_URL') or "http://localhost:4566"
dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
table = dynamodb.Table('Orders')

def lambda_handler(event, context):
    try:
        # Mengakomodasi input langsung atau lewat proxy API Gateway
        body = event if not event.get('body') else json.loads(event['body'])
        order_id = str(uuid.uuid4())[:8]
        
        item = {
            'orderId': order_id,
            'customer': body.get('customer', 'Ahya'),
            'product': body.get('product', 'Mechanical Keyboard'),
            'quantity': int(body.get('quantity', 1)),
            'status': 'PENDING'
        }
        
        # HANYA menulis ke DynamoDB (Menghindari masalah Dual-Write)
        table.put_item(Item=item)
        
        return {
            "statusCode": 202,
            "body": json.dumps({"orderId": order_id, "status": "PENDING"})
        }
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}