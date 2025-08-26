from app.service.baidu_ads_data_capture_serivce import BaiduAdsDataCaptureService



def run():
    baidu_ads_data_capture_service = BaiduAdsDataCaptureService("金蛛账户中心")
    baidu_ads_data_capture_service.run()



if __name__ == "__main__":
    run()




