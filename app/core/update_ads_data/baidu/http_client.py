import httpx
from ....utils import retry

@retry()
def refresh_access_http_client(app_id:str,secret_key:str,refresh_token:str,user_id:str):
    with httpx.Client() as client:
        url = "https://u.baidu.com/oauth/refreshToken"
        headers = {
            "Content-Type": "application/json;charset:utf-8;",
        }
        params = {
            "appId": app_id,
            "refreshToken": refresh_token,
            "secretKey": secret_key,
            "userId": user_id,
        }
        response = client.post(url, headers=headers, json=params)
        response.raise_for_status()
        return response.json()
