# -*- coding: gbk -*-
import json as js
import requests
import uuid
import random
from faker import Faker
import time
import _thread


def random_str():
    seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    sa = []
    # 5可以改, 5是新目录字符长度
    for i in range(5):
        sa.append(random.choice(seed))
    salt = ''.join(sa)
    return salt


def get_ms_token(username, password, tenant):
    url = "https://login.microsoftonline.com/" + tenant + "/oauth2/token"
    header = {
        "Content-Type": "application/x-www-form-urlencoded "
    }
    post_data = {
        "grant_type": "password",
        "resource": "74658136-14ec-4630-ad9b-26e160ff0fc6",
        "client_id": "1950a258-227b-4e31-a9cf-717495945fc2",
        "username": username,
        "password": password
    }
    x = requests.post(url, headers=header, data=post_data)
    try:
        json = js.loads(x.text)
        results = json["access_token"]
    except:
        time.sleep(300)
        # 防止目录返回错误
        results = get_ms_token(username, password, tenant)
    return results


def check_dic_avl(dic_name, token):
    url = 'https://main.iam.ad.ext.azure.com/api/Directories/DomainAvailability/' + dic_name
    header = {
        'Authorization': 'Bearer ' + token,
        "x-ms-client-request-id": str(uuid.uuid1()),
        "x-ms-effective-locale": "zh-hans.zh-cn"
    }
    x = requests.get(url, headers=header)
    if x.text == "true":
        return True
    else:
        return False


def create_tenant(dic_name, token):
    url = "https://main.iam.ad.ext.azure.com/api/Directories"
    header = {
        'Authorization': 'Bearer ' + token,
        "x-ms-client-request-id": str(uuid.uuid1()),
        "x-ms-effective-locale": "zh-hans.zh-cn"
    }
    post_data = {
        "companyName": dic_name,
        "countryCode": "US",
        "initialDomainPrefix": dic_name
    }
    x = requests.post(url, json=post_data, headers=header)
    return x.text


def create_user(dic_name, password, token):
    url = 'https://main.iam.ad.ext.azure.com/api/UserDetails'
    post_data = {
        "accountEnabled": True,
        "displayName": faker.name(),
        "usageLocation": "US",
        "userPrincipalName": "admin@" + dic_name + ".onmicrosoft.com",
        "passwordProfile":
            {
                "password": password,
                "forceChangePasswordNextLogin": False
            },
        "selectedGroupIds": [],
        "selectedRoleIds": ["62e90394-69f5-4237-9190-012177145e10"],
        "rolesEntity": None
    }
    header = {
        'Authorization': 'Bearer ' + token,
        "x-ms-client-request-id": str(uuid.uuid1()),
        "x-ms-effective-locale": "zh-hans.zh-cn"
    }
    x = requests.post(url, headers=header, json=post_data)
    json = js.loads(x.text)
    if "accountEnabled" in json:
        return True
    else:
        return False


def get_temp_pass(token):
    url = 'https://main.iam.ad.ext.azure.com/api/User/TemporaryPassword'
    header = {
        'Authorization': 'Bearer ' + token,
        "x-ms-client-request-id": str(uuid.uuid1()),
        "x-ms-effective-locale": "zh-hans.zh-cn"
    }
    x = requests.get(url, headers=header)
    return x.text.replace('"', '')


def check_user_name(dic_name, token):
    url = 'https://main.iam.ad.ext.azure.com/api/Users/IsUPNUniqueOrPending/admin%40' + dic_name + '.onmicrosoft.com'
    header = {
        'Authorization': 'Bearer ' + token,
        "x-ms-client-request-id": str(uuid.uuid1()),
        "x-ms-effective-locale": "zh-hans.zh-cn"
    }
    x = requests.get(url, headers=header)
    return


def get_old_admin_uuid(token):
    url = 'https://main.iam.ad.ext.azure.com/api/Users?searchText=&top=25&orderByThumbnails=false&maxThumbnailCount=999&filterValue=All&state=All&adminUnit='
    header = {
        'Authorization': 'Bearer ' + token,
        "x-ms-client-request-id": str(uuid.uuid1()),
        "x-ms-effective-locale": "zh-hans.zh-cn"
    }
    x = requests.post(url, headers=header)
    json = js.loads(x.text)
    while "items" not in json:
        time.sleep(60)
        x = requests.post(url, headers=header)
        json = js.loads(x.text)
    return json["items"][0]["objectId"]


def delete_account_t(username, password, tenant):
    token = get_ms_token(username, password, tenant)
    old_account = get_old_admin_uuid(token)
    delete_account(token, old_account)
    line = username + ";" + password
    print(line)
    with open("us.txt", "a") as write:
        write.write(line + "\n")


def delete_account(token, object_id):
    url = "https://main.iam.ad.ext.azure.com/api/Users"
    header = {
        'Authorization': 'Bearer ' + token,
        "x-ms-client-request-id": str(uuid.uuid1()),
        "x-ms-effective-locale": "zh-hans.zh-cn"
    }
    data = [object_id]
    x = requests.delete(url, json=data, headers=header)
    url = "https://main.iam.ad.ext.azure.com/api/Users/PermanentDelete"
    x = requests.delete(url, json=data, headers=header)


def run():
    global count
    token = get_ms_token(admin_username, admin_password, default_tenant)
    dic_name = random_str()
    while not check_dic_avl(dic_name, token):
        dic_name = random_str()
    new_tenant = create_tenant(dic_name, token)
    new_tenant = new_tenant.replace('"', '')
    token = get_ms_token(admin_username, admin_password, new_tenant)
    password = get_temp_pass(token)
    if create_user(dic_name, password, token):
        count += 1
        line = "admin@" + dic_name + ".onmicrosoft.com" + ";" + password + ";" + new_tenant
        # ↓ 这里只是临时记录一下，可以删掉
        with open("us_n.txt", "a") as write:
            write.write(line + "\n")
        print(line)
        time.sleep(60)
        _thread.start_new_thread(delete_account_t, ("admin@" + dic_name + ".onmicrosoft.com", password, new_tenant))
    if count < max_count:
        run()


faker = Faker("en_US")
max_count = 1000
# 最多账号数量
thread_count = 20
# 线程数量
count = 0
admin_username = ''
admin_password = ''
default_tenant = ''
# 全局管理员账号密码和租户ID 租户ID这里看 ↓
# https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade  打开终结点 "https://login.microsoftonline.com/" 和 “/oauth2/authorize”  之间的就是

for i in range(thread_count):
    _thread.start_new_thread(run, ())

while True:
    pass
