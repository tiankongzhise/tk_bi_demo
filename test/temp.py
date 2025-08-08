from app.service.baidu_ads_data_capture_serivce import BaiduAdsDataCaptureService



def run():
    baidu_ads_data_capture_service = BaiduAdsDataCaptureService("金蛛账户中心")
    baidu_ads_data_capture_service.oauth()
    report_task = baidu_ads_data_capture_service.get_ads_report_data("金蛛-新账户5","keyword_day")
    print(report_task)


if __name__ == '__main__':
    run()

