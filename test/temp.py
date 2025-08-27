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
    
if __name__ == '__main__':
    # test_get_changed_scale()
    # test_choose_get_objects_function()
    # test_get_changed_objects()
    # test_get_objects_status()
    test_get_objects_file_path()
