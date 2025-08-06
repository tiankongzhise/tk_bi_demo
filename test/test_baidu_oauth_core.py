from app.core import BaiduOauthCore



def test():
    baidu_oauth_core = BaiduOauthCore('金蛛账户中心')
    result = baidu_oauth_core.oauth()
    print(result)
    
if __name__ == '__main__':
    test()
