import sys
import jwt
import json
import datetime
import base64

auth0_api_roles = ['users', 'users_app_metadata', 'clients', 'client_grants',
                   'client_keys', 'connections', 'email_provider', 'rules']
auth0_api_roles_actions = ["read", "update", "delete", "create"]

def create_scope():
    scopes = dict()
    for role in auth0_api_roles:
        scopes[role] = dict(actions=auth0_api_roles_actions)
    return scopes

def generate_token(dir):
    with open(dir +'/conf.json', 'r') as fr:
        json_data = json.load(fr)
        api_key = json_data['api_key']

        global_secret = json_data['global_token']
        payload = dict(scopes=create_scope(),
                       aud=api_key,
                       iat= datetime.datetime.utcnow()
                       )
        token = jwt.encode(payload,
                           base64.b64decode(global_secret.replace("_","/").replace("-","+")),
                           algorithm='HS256', headers={'audience': api_key})
        with open(dir +'/token', 'w') as fw:
            fw.write(token)

if __name__ == '__main__':
    jwt_dir = sys.argv[1]
    generate_token(jwt_dir)
