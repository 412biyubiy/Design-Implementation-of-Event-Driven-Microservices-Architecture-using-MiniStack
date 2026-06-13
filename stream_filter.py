# stream_filter.py
import json
import boto3
import os

endpoint_url = os.environ.get('AWS_ENDPOINT_URL') or "http://localhost:4566"
sqs = boto3.client('sqs', endpoint_url=endpoint_url)

# Ambil Queue URL internal
QUEUE_URL = f"http://{os.environ.get('LOCALSTACK_HOSTNAME', 'localhost')}:4566/000000000000/order-processing-queue"

def lambda_handler(event, context):
    for record in event.get('Records', []):
        # FILTER: Hanya loloskan data baru masuk (INSERT) dengan status PENDING
        if record['eventName'] == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            status = new_image['status']['S']
            
            if status == 'PENDING':
                order_id = new_image['orderId']['S']
                message_body = json.dumps({"orderId": order_id})
                
                sqs.send_message(
                    QueueUrl=QUEUE_URL,
                    MessageBody=message_body
                )
                print(f"[StreamFilter] Sent order {order_id} to SQS Queue.")
                
    return {"statusCode": 200}