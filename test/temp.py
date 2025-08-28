import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.local_file_io import get_gz_file_data,save_to_txt
from app.core import FetchStructureBaiduCore,BaiduOauthCore
from pathlib import Path

def test_file_path():
    oauth_core = BaiduOauthCore("金蛛账户中心")
    oauth_info = oauth_core.oauth()
    fetch_structure_baidu_client = FetchStructureBaiduCore(access_token=oauth_info.access_token,user_name="金蛛-新账户5",temp_dir="./downloads")
    rsp = fetch_structure_baidu_client.run(download_all_objects=True)
    print(rsp)
    return rsp


def test_get_gz_data(file_path:str):
    file_path = Path(file_path)
    data = get_gz_file_data(file_path)
    if data.status == 'success':
       save_file_path = save_to_txt(data.data, file_path.with_suffix('.txt'))
       print(f'数据已保存到{save_file_path}')
    else:
        print(data.msg)

if __name__ == '__main__':
    rsp = test_file_path()
    for file_path in rsp.get('success_files',[]):
        test_get_gz_data(file_path)
    

