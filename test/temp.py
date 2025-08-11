from app.core import BaiduOauthCore
from app.core import FetchAdsDataBaiduCore



def run():
    baidu_oauth_core = BaiduOauthCore("金蛛账户中心")
    baidu_oauth_credentials = baidu_oauth_core.oauth()
    access_token = baidu_oauth_credentials.access_token
    fetch_ads_data_baidu_core = FetchAdsDataBaiduCore(access_token,"金蛛-新账户5")

    fetch_ads_data_baidu_core.run("keyword_day")



if __name__ == '__main__':
    run()

