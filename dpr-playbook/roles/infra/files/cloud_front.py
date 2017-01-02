# coding=utf-8
import boto3
import json
import argparse

def list_distributions(cf):
    response = cf.list_distributions()
    print response

def parse_arg():
    parser = argparse.ArgumentParser(description='Api gateway')
    parser.add_argument("op", help='operation list/put')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arg()
    client = boto3.client('cloudfront')
    if args.op == 'list':
        list_distributions(client)
