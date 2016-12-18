import boto3

client = boto3.client('apigateway')

def create_domain(ag, domain_name, cert_name, cert_body,
                  cert_private_key, cert_chain):
    response = ag.create_domain_name(
                    domainName=domain_name,
                    certificateName=cert_name,
                    certificateBody=cert_body,
                    certificatePrivateKey=cert_private_key,
                    certificateChain=cert_chain)


def get_domain(ag, domain_name):
    response = ag.get_domain_name(domain_name)
