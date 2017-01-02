# coding=utf-8
import boto3
import argparse


def create_domain(ag, domain_name, cert_name, cert_body,
                  cert_private_key, cert_chain):
    response = ag.create_domain_name(
                    domainName=domain_name,
                    certificateName=cert_name,
                    certificateBody=cert_body,
                    certificatePrivateKey=cert_private_key,
                    certificateChain=cert_chain)
    print (response)


def get_domain(ag, domain_name):
    response = ag.get_domain_names()
    if 'items' in response:
        for item in response['items']:
            if domain_name == item['domainName']:
                return True
    return False
ck = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAqqymAq5y0mkM4N8rMiQg80F6OmlKYRuO3HGCXT5o6+cBexTb
vjPL7UaYfP9g0303Ky44KWfa7gzvAxPQU3rf2q6W1+5OiRuuYVBpTt+V59m+D5PE
76Fw//Sbisn4qlUHORCpvmDwRazXrPjvheZICtKfMgFwfLc1E+QLNlvOnbsh6LN6
muRHYcf02bee9Kil7QxDdrOzEgZoDo2g/l4C54LfN4WwBkFgbBKKtgfoD/QEAC6m
7tdSSXb4SVpx1Xz5/VR3nvQk8Dx2L6Jb3fVL+Y7J+gYDrMJBZg0KwJYjNKLt0gG2
DoTfuPH9RcDd6nistdtjLVCEUGVTGqQB/k3MBQIDAQABAoIBAQCf0ztGiYwWw67+
qZ2uv6xnf2pxZoXzd7YJcvYsUTQ5rMJzOu4oKCMQWCqV6yQGCFzwP8Dx7UJT56Ku
1BAjDI6yHwo8vPmoZVaf5IgpBzE+w2W6+prR9/F0juBVUJtfDm7MHnGGSQrXhGsX
nKnYTvQpxmCzmCt5bqryrHtfdQuAId/PdAsEZoLvLvNUEGU+uJRFq+6DFq4yXqS0
yxPZ20JC0PGfxVOb3Ex2E69hjSyvyokpeL+4R/ns90V+yPk8G7TfZGKUrsV09XjG
vgNLT2sa8AinjZXsxVcsTfM33bWPnDnmwacu2A8zNM3hVL1feka4VwrtvCjRzP0v
SqDtvWQFAoGBAPTnw5dUHGVEG+TZGwTAneE0JBi7ermJO080NBPsM4Vm4i5tVfu3
06vhotyq79bZqn1gPqGeYokNBSoL8uklA8Cb6jZSJtp7+WFUAt8KinMDVyPhoaoL
gg4fA2xJIYQuevrMsUiRQ6ygaVJ41feL0FXmmkzg01h2jqwfSn8LnfMvAoGBALJo
AfGQ0N8CcBa/Vd0AuQBr76/lwLrtI9nBV+z7rYH6XiOWKVVFCgmtLcdoiL0Vmo8J
0LBeZvyDyDz/UfwSoCwQroCu88zX50VpWpfpyy/zHQISNYQwTmEDf6uVBbt87pdR
XjwwrzGbBaUKDOGFkLMAkabGQ0mNFh+lNTYkvvcLAoGBAA6CqOEPd7s8RNbTUjl+
3BvaxgS9HvFdQylXM3q2tPrDdMVBbyXB54W4kbi3XAyDywkwqaVTyAzMu7CZEqRj
sAw6cK8VQP4S+Fye6KikbD2SRhh3Juf3VJZXmhFRZ+33/wtbE2n0SWkx++uKA0tu
ekKMrjm93GfSZnOmSviqDIq7AoGAcJG/6DSAFrbrEu9XtkMmeGWir1JA8bF/1X5x
hE6phEH99GZjXjJZyxFCuXf0D5r6ExcWXrKyONLOHe7cRDlcZ3F/KiM6Ih55Bwsa
5o/WbULxIsVqjyYLzprui81T+KEzyrbExyXQ5XPzc9eLmSE11DyfqqOfAWHMe9s6
YBd/h1ECgYA89IgJlSUns0ctq4Z5wxbQEsmDpzgofIdpbh5nrPO/dLCAS9HZbvq9
OCwZd0EZ11pLv++JBFJ9vWS63GpShLA5zMvs00ULoYETyTrgc6rKbQHHimVr5OLL
U6DJPJDNOEjMWFKPgTUYPDFgBdqy1pHzM+DmCB+cR/7XxWhOvz6jsA==
-----END RSA PRIVATE KEY-----

"""
cb = """
-----BEGIN CERTIFICATE-----
MIIFADCCA+igAwIBAgISA2vdtC/nGh95/PwttXTJ5z12MA0GCSqGSIb3DQEBCwUA
MEoxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MSMwIQYDVQQD
ExpMZXQncyBFbmNyeXB0IEF1dGhvcml0eSBYMzAeFw0xNjEyMTcxNzM5MDBaFw0x
NzAzMTcxNzM5MDBaMBkxFzAVBgNVBAMTDnN1YmhhbmthcmIuY29tMIIBIjANBgkq
hkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqqymAq5y0mkM4N8rMiQg80F6OmlKYRuO
3HGCXT5o6+cBexTbvjPL7UaYfP9g0303Ky44KWfa7gzvAxPQU3rf2q6W1+5OiRuu
YVBpTt+V59m+D5PE76Fw//Sbisn4qlUHORCpvmDwRazXrPjvheZICtKfMgFwfLc1
E+QLNlvOnbsh6LN6muRHYcf02bee9Kil7QxDdrOzEgZoDo2g/l4C54LfN4WwBkFg
bBKKtgfoD/QEAC6m7tdSSXb4SVpx1Xz5/VR3nvQk8Dx2L6Jb3fVL+Y7J+gYDrMJB
Zg0KwJYjNKLt0gG2DoTfuPH9RcDd6nistdtjLVCEUGVTGqQB/k3MBQIDAQABo4IC
DzCCAgswDgYDVR0PAQH/BAQDAgWgMB0GA1UdJQQWMBQGCCsGAQUFBwMBBggrBgEF
BQcDAjAMBgNVHRMBAf8EAjAAMB0GA1UdDgQWBBQo+RUD1iGXPc9AYti8V3Kdv0Xl
HjAfBgNVHSMEGDAWgBSoSmpjBH3duubRObemRWXv86jsoTBwBggrBgEFBQcBAQRk
MGIwLwYIKwYBBQUHMAGGI2h0dHA6Ly9vY3NwLmludC14My5sZXRzZW5jcnlwdC5v
cmcvMC8GCCsGAQUFBzAChiNodHRwOi8vY2VydC5pbnQteDMubGV0c2VuY3J5cHQu
b3JnLzAZBgNVHREEEjAQgg5zdWJoYW5rYXJiLmNvbTCB/gYDVR0gBIH2MIHzMAgG
BmeBDAECATCB5gYLKwYBBAGC3xMBAQEwgdYwJgYIKwYBBQUHAgEWGmh0dHA6Ly9j
cHMubGV0c2VuY3J5cHQub3JnMIGrBggrBgEFBQcCAjCBngyBm1RoaXMgQ2VydGlm
aWNhdGUgbWF5IG9ubHkgYmUgcmVsaWVkIHVwb24gYnkgUmVseWluZyBQYXJ0aWVz
IGFuZCBvbmx5IGluIGFjY29yZGFuY2Ugd2l0aCB0aGUgQ2VydGlmaWNhdGUgUG9s
aWN5IGZvdW5kIGF0IGh0dHBzOi8vbGV0c2VuY3J5cHQub3JnL3JlcG9zaXRvcnkv
MA0GCSqGSIb3DQEBCwUAA4IBAQAC8Ro56g/NwylLjuk/u2z3lgv865jjGY3icyYj
v/3mktbdEsHH9uuySen4HizQzpog8WNi2uz9QserY88BQdGme1hcD21s2UmRHYd4
ueAs42plP8aXbES2Ga+8KCbNtIdMCbChtp9jpxnzRUToMHUbrX33RqtL/ffCmf95
nbbFSzM/PcDnGG+5KgZeFS1RYnMwTXAJ9EShTusmPiBHudpGcPbxF03D8utoD4nU
GH97aqxNdQ7xj5vk5mii4s4sje5GQF0j57HdbISksiMqmHXPR2YqPXp4jm/DO6I0
v40xoGmRgvAgcv5b4iJvoOKGB4MWKTne2/Jcs1apFXCnJLak
-----END CERTIFICATE-----

"""
cc = """
-----BEGIN CERTIFICATE-----
MIIEkjCCA3qgAwIBAgIQCgFBQgAAAVOFc2oLheynCDANBgkqhkiG9w0BAQsFADA/
MSQwIgYDVQQKExtEaWdpdGFsIFNpZ25hdHVyZSBUcnVzdCBDby4xFzAVBgNVBAMT
DkRTVCBSb290IENBIFgzMB4XDTE2MDMxNzE2NDA0NloXDTIxMDMxNzE2NDA0Nlow
SjELMAkGA1UEBhMCVVMxFjAUBgNVBAoTDUxldCdzIEVuY3J5cHQxIzAhBgNVBAMT
GkxldCdzIEVuY3J5cHQgQXV0aG9yaXR5IFgzMIIBIjANBgkqhkiG9w0BAQEFAAOC
AQ8AMIIBCgKCAQEAnNMM8FrlLke3cl03g7NoYzDq1zUmGSXhvb418XCSL7e4S0EF
q6meNQhY7LEqxGiHC6PjdeTm86dicbp5gWAf15Gan/PQeGdxyGkOlZHP/uaZ6WA8
SMx+yk13EiSdRxta67nsHjcAHJyse6cF6s5K671B5TaYucv9bTyWaN8jKkKQDIZ0
Z8h/pZq4UmEUEz9l6YKHy9v6Dlb2honzhT+Xhq+w3Brvaw2VFn3EK6BlspkENnWA
a6xK8xuQSXgvopZPKiAlKQTGdMDQMc2PMTiVFrqoM7hD8bEfwzB/onkxEz0tNvjj
/PIzark5McWvxI0NHWQWM6r6hCm21AvA2H3DkwIDAQABo4IBfTCCAXkwEgYDVR0T
AQH/BAgwBgEB/wIBADAOBgNVHQ8BAf8EBAMCAYYwfwYIKwYBBQUHAQEEczBxMDIG
CCsGAQUFBzABhiZodHRwOi8vaXNyZy50cnVzdGlkLm9jc3AuaWRlbnRydXN0LmNv
bTA7BggrBgEFBQcwAoYvaHR0cDovL2FwcHMuaWRlbnRydXN0LmNvbS9yb290cy9k
c3Ryb290Y2F4My5wN2MwHwYDVR0jBBgwFoAUxKexpHsscfrb4UuQdf/EFWCFiRAw
VAYDVR0gBE0wSzAIBgZngQwBAgEwPwYLKwYBBAGC3xMBAQEwMDAuBggrBgEFBQcC
ARYiaHR0cDovL2Nwcy5yb290LXgxLmxldHNlbmNyeXB0Lm9yZzA8BgNVHR8ENTAz
MDGgL6AthitodHRwOi8vY3JsLmlkZW50cnVzdC5jb20vRFNUUk9PVENBWDNDUkwu
Y3JsMB0GA1UdDgQWBBSoSmpjBH3duubRObemRWXv86jsoTANBgkqhkiG9w0BAQsF
AAOCAQEA3TPXEfNjWDjdGBX7CVW+dla5cEilaUcne8IkCJLxWh9KEik3JHRRHGJo
uM2VcGfl96S8TihRzZvoroed6ti6WqEBmtzw3Wodatg+VyOeph4EYpr/1wXKtx8/
wApIvJSwtmVi4MFU5aMqrSDE6ea73Mj2tcMyo5jMd6jmeWUHK8so/joWUoHOUgwu
X4Po1QYz+3dszkDqMp4fklxBwXRsW10KXzPMTZ+sOPAveyxindmjkW8lGy+QsRlG
PfZ+G6Z6h7mjem0Y+iWlkYcV4PIWL1iwBi8saCbGS5jN2p8M+X+Q7UNKEkROb3N6
KOqkqm57TH2H3eDJAkSnh6/DNFu0Qg==
-----END CERTIFICATE-----
"""


def mapping_domain_to_lambda(ag, domain_name, api_id, environment_tier):
    res = ag.create_base_path_mapping(
        domainName=domain_name,
        basePath='',
        restApiId=api_id,
        stage=environment_tier)
    print (res)


def get_rest_api_ids(ag, api_name_prefix, environment_tier):
    apis = ag.get_rest_apis()
    api_ids = []
    if 'items' in apis:
        for item in apis['items']:
            name = item['name']
            if name.startswith(api_name_prefix) and name.endswith(environment_tier):
                api_ids.append(item['id'])
    return api_ids


def parse_arg():
    parser = argparse.ArgumentParser(description='Api gateway')
    parser.add_argument("op", help='operation cd=create domain/cm= create mapping/dd= delete domain/dm=delete mapping')
    parser.add_argument("--dn", help='domain name', default='subhankarb.com')
    parser.add_argument("--cb", help='certificate body', default=cb)
    parser.add_argument("--ck", help='certificate private key', default=ck)
    parser.add_argument("--cc", help='certificate chain', default=cc)
    parser.add_argument("--anp", help='api name prefix', default='dpr-api')
    parser.add_argument("--et", help='environment tier', default='development')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arg()
    client = boto3.client('apigateway')

    if args.op == 'cd':
        status = get_domain(client, args.dn)  # dpr-api.subhankarb.com
        if not status:
            create_domain(client, args.dn, args.dn + "-generated-ansible", args.cb, args.ck, args.cc)
    if args.op == 'cm':
        ids = get_rest_api_ids(client, args.anp, args.et)
        for api_id in ids:
            mapping_domain_to_lambda(client, args.dn, api_id, args.et)
    if args.op == 'dm':
        client.delete_base_path_mapping(domainName=args.dn)

    if args.op == 'dd':
        client.delete_domain_name(domainName=args.dn)
