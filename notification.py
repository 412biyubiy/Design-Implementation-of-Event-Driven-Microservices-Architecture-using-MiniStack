import json
import boto3
import os

# Gunakan env variable LocalStack jika ada, kalau ga ada arahkan ke localhost
localstack_host = os.environ.get('LOCALSTACK_HOSTNAME', 'localhost')
ses_client = boto3.client('ses', endpoint_url=f'http://{localstack_host}:4566', region_name='us-east-1')

def lambda_handler(event, context):
    for record in event['Records']:
        # Pastikan ini adalah event modifikasi data
        if record['eventName'] == 'MODIFY':
            new_image = record['dynamodb']['NewImage']
            
            order_id = new_image['orderId']['S']
            status = new_image['status']['S']
            customer = new_image['customer']['S']
            product = new_image['product']['S']
            
            # CRITICAL FILTER: Cuma kirim email kalau statusnya berubah jadi COMPLETED
            if status == 'COMPLETED':
                print(f"[Notification] Order {order_id} is COMPLETED. Sending email via SES...")
                
                try:
                    response = ses_client.send_email(
                        Source='store@example.com',
                        Destination={'ToAddresses': ['ahya@example.com']},
                        Message={
                            'Subject': {'Data': f'Nota Pembelian Order {order_id}'},
                            'Body': {
                                'Text': {
                                    'Data': f'Halo {customer},\n\nPesanan {product} lu dengan Order ID {order_id} telah berhasil diproses dan statusnya kini COMPLETED!\n\nTerima kasih sudah berbelanja.'
                                }
                            }
                        }
                    )
                    print(f"[Notification] Email successfully sent! MessageId: {response['MessageId']}")
                except Exception as e:
                    print(f"[Notification] ERROR sending email: {str(e)}")
                    
    return {"statusCode": 200, "body": "Notification processed"}