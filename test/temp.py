from app.core import FetchStructureBaiduCore
from app.core import BaiduOauthCore


def test_get_changed_scale():
    oauth_core = BaiduOauthCore("金蛛账户中心")
    oauth_info = oauth_core.oauth()
    fetch_structure_baidu_client = FetchStructureBaiduCore(access_token=oauth_info.access_token,user_name="金蛛-新账户5",temp_dir="./download")
    changeed_scale = fetch_structure_baidu_client.get_changed_scale()
    print(changeed_scale)

def test_choose_get_objects_function():
    oauth_core = BaiduOauthCore("金蛛账户中心")
    oauth_info = oauth_core.oauth()
    fetch_structure_baidu_client = FetchStructureBaiduCore(access_token=oauth_info.access_token,user_name="金蛛-新账户5",temp_dir="./download")
    get_objects_function = fetch_structure_baidu_client.choose_get_objects_function()
    print(get_objects_function)

def test_get_changed_objects():
    oauth_core = BaiduOauthCore("金蛛账户中心")
    oauth_info = oauth_core.oauth()
    fetch_structure_baidu_client = FetchStructureBaiduCore(access_token=oauth_info.access_token,user_name="金蛛-新账户5",temp_dir="./download")
    rsp = fetch_structure_baidu_client.get_changed_objects()
    print(rsp)

def test_get_objects_status():
    oauth_core = BaiduOauthCore("金蛛账户中心")
    oauth_info = oauth_core.oauth()
    fetch_structure_baidu_client = FetchStructureBaiduCore(access_token=oauth_info.access_token,user_name="金蛛-新账户5",temp_dir="./download")
    rsp = fetch_structure_baidu_client.get_objects_status(file_id="c06a9f3460114580dd5a0bcb6924928e")
    print(rsp)

def test_get_objects_file_path():
    oauth_core = BaiduOauthCore("金蛛账户中心")
    oauth_info = oauth_core.oauth()
    fetch_structure_baidu_client = FetchStructureBaiduCore(access_token=oauth_info.access_token,user_name="金蛛-新账户5",temp_dir="./download")
    rsp = fetch_structure_baidu_client.get_objects_file_path(file_id="c06a9f3460114580dd5a0bcb6924928e")
    print(rsp)

def test_download_objects():
    temp_dict = {'campaignFilePath': 'https://apidata.baidu.com/v1/api-bulkjob/bulkjob-material/api/2025-08-27/64951865/fc/inc/c06a9f3460114580dd5a0bcb6924928e/meta/64951865-fc-inc-campaign-c06a9f3460114580dd5a0bcb6924928e-campaign-0.gz?authorization=bce-auth-v1%2F62c5b6f33bf14302b4d2cd6a12cfd1df%2F2025-08-27T07%3A59%3A40Z%2F259200%2F%2Fa0c31f834586af7a8ede735069a23d7d29a365ec399d27dfbd1d051799b48fe3', 'adgroupFilePath': 'https://apidata.baidu.com/v1/api-bulkjob/bulkjob-material/api/2025-08-27/64951865/fc/inc/c06a9f3460114580dd5a0bcb6924928e/meta/64951865-fc-inc-adgroup-c06a9f3460114580dd5a0bcb6924928e-adgroup-0.gz?authorization=bce-auth-v1%2F62c5b6f33bf14302b4d2cd6a12cfd1df%2F2025-08-27T07%3A59%3A40Z%2F259200%2F%2F6054b6c370bed9e78cbc9b7ed0a7a1edf1177099ce9cce22217db842e03dd291', 'keywordFilePath': 'https://apidata.baidu.com/v1/api-bulkjob/bulkjob-material/api/2025-08-27/64951865/fc/inc/c06a9f3460114580dd5a0bcb6924928e/meta/64951865-fc-inc-keyword-c06a9f3460114580dd5a0bcb6924928e-keyword-0.gz?authorization=bce-auth-v1%2F62c5b6f33bf14302b4d2cd6a12cfd1df%2F2025-08-27T07%3A59%3A43Z%2F259200%2F%2F95725608a5697d81906fdcd39eaf4f25c885b412d48cc44970f8b58233d40923', 'creativeFilePath': 'https://apidata.baidu.com/v1/api-bulkjob/bulkjob-material/api/2025-08-27/64951865/fc/inc/c06a9f3460114580dd5a0bcb6924928e/meta/64951865-fc-inc-creative-c06a9f3460114580dd5a0bcb6924928e-creative-0.gz?authorization=bce-auth-v1%2F62c5b6f33bf14302b4d2cd6a12cfd1df%2F2025-08-27T07%3A59%3A40Z%2F259200%2F%2F60f37b23b3a389880c51c861eba4cfbe6ab7571aa09adcaf055ef0577ced7254', 'autoExpansionFilePath': 'https://apidata.baidu.com/v1/api-bulkjob/bulkjob-material/api/2025-08-27/64951865/fc/inc/c06a9f3460114580dd5a0bcb6924928e/meta/64951865-fc-inc-autoExpansion-c06a9f3460114580dd5a0bcb6924928e-autoExpansion-0.gz?authorization=bce-auth-v1%2F62c5b6f33bf14302b4d2cd6a12cfd1df%2F2025-08-27T07%3A59%3A40Z%2F259200%2F%2Fa6a692d41139c506bd09501462709d359dbde160ba5dfbda535d50f1be01b80c', 'campaignFileMd5': '9e3ca57ec05cad5f0669ccd5581c1e29', 'adgroupFileMd5': 'df50ce571837b382089a15a07036ae31', 'keywordFileMd5': '06864c0e9a31eec86e4d30b113088bac', 'creativeFileMd5': '530f25ded77600eaf31cc177268a5099', 'autoExpansionFileMd5': '2561681b72908c6021345470ac92d866'}

    oauth_core = BaiduOauthCore("金蛛账户中心")
    oauth_info = oauth_core.oauth()
    fetch_structure_baidu_client = FetchStructureBaiduCore(access_token=oauth_info.access_token,user_name="金蛛-新账户5",temp_dir="./download")
    rsp = fetch_structure_baidu_client.download_objects(temp_dict)
    print(rsp)
    
if __name__ == '__main__':
    # test_get_changed_scale()
    # test_choose_get_objects_function()
    # test_get_changed_objects()
    # test_get_objects_status()
    # test_get_objects_file_path()
    test_download_objects()
