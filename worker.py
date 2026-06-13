# worker.py
import json
import boto3
import os
import time

endpoint_url = os.environ.get('AWS_ENDPOINT_URL') or "http://localhost:4566"
dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
table = dynamodb.Table('Orders')
ses = boto3.client('ses', endpoint_url=endpoint_url)

def lambda_handler(event, context):
    for record in event.get('Records', []):
        body = json.loads(record['body'])
        order_id = body['orderId']
        
        print(f"[Worker] Processing order {order_id}...")
        
        # IDEMPOTENCY CHECK & UPDATE: Set status ke PROCESSING
        table.update_item(
            Key={'orderId': order_id},
            UpdateExpression="set #s = :s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'PROCESSING'}
        )
        
        # Simulasi proses rakit pesanan
        time.sleep(3)
        
        # UPDATE: Set status ke COMPLETED
        table.update_item(
            Key={'orderId': order_id},
            UpdateExpression="set #s = :s",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'COMPLETED'}
        )
        print(f"[Worker] Order {order_id} marked as COMPLETED.")
        
        # Mock Kirim Email via SES
        try:
            ses.send_email(
                Source='store@example.com',
                Destination={'ToAddresses': ['customer@example.com']},
                Message={
                    'Subject': {'Data': f'Order {order_id} Sukses!'},
                    'Body': {'Text': {'Data': f'Halo, pesanan {order_id} lu udah beres dirakit.'}}
                }
            )
            print(f"[Worker] Mock Email sent for order {order_id}")
        except Exception as e:
            print(f"[Worker] SES Error: {str(e)}")
            
    return {"statusCode": 200}