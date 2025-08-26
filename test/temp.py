from app.core import BaiduOauthCore
from app.core import FetchStructureBaiduCore
from app.kernel import BaiduHttpClient

def test_fetch_structure_baidu():
    oauth_core = BaiduOauthCore("金蛛账户中心")
    oauth_info = oauth_core.oauth()
    # fetch_structure_baidu = FetchStructureBaiduCore(access_token=oauth_info.access_token,user_name="金蛛-新账户5",temp_dir="./temp")
    baidu_api_client = BaiduHttpClient()
    baidu_api_client.set_oauth_account(user_name="金蛛-新账户5",access_token=oauth_info.access_token)
    # rsp = baidu_api_client.get_changed_scale('2025-07-01')
    
    search_level_list = ['campaign','adgroup','keyword','creative','autoExpansion']
    feed_level_list = ['campaignFeed','adgroupFeed','creativeFeed','atpFeed']
    query_level = 'campaign'
    # query_by_page = {
    #     'pageNo':1,
    #     'pageSize':20000,
    #     f'{query_level}Level':True
    # }
    # query_by_page.update({
    #     f'{level}Level':False for level in search_level_list if level != query_level
    # })
    
    # query_by_page = {
    #     # 'pageNo':1,
    #     # 'pageSize':20000,
    #     'mobileExtend':1,
    # }
    # query_by_page.update({
    #     f'{level}Fields':["all"] for level in search_level_list
    # })
    # print(f'query_by_page:{query_by_page}')
    # rsp = baidu_api_client.get_all_changed_objects('2025-07-01',**query_by_page)
    # rsp = baidu_api_client.get_all_objects(**query_by_page)
    
    # rsp = baidu_api_client.get_file_status('39fa0bebf47b1b5e4b6363443d9dd3fd')
    
    rsp = baidu_api_client.get_file_path('39fa0bebf47b1b5e4b6363443d9dd3fd')
    return rsp

if __name__ == '__main__':
    rsp = test_fetch_structure_baidu()
    print(rsp)
