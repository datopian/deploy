# coding=utf-8
import boto3
import json
import argparse


def put_cors(s3, bucket, payload):
    response = s3.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration=json.loads(payload)
    )
    print response

def get_cors(s3, bucket):
    response = s3.get_bucket_cors(Bucket=bucket)
    print response

def parse_arg():
    parser = argparse.ArgumentParser(description='Api gateway')
    parser.add_argument("op", help='operation get/put')
    parser.add_argument("-b", "--bucket", help='cors bucket')
    parser.add_argument("-p", "--payload", help='cors payload')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arg()
    client = boto3.client('s3')
    if args.op == 'put':
        put_cors(client, args.bucket, args.payload)
    elif args.op == 'get':
        get_cors(client, args.bucket)
