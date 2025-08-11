from app.service.baidu_ads_data_capture_serivce import BaiduAdsDataCaptureService
from app.core.fetch_ads_data_baidu import FetchAdsDataBaiduCore
from app.core.bd_oauth import BaiduOauthCore


def test_accept_both_cases_fix():
    """测试accept_both_cases装饰器修复后的功能"""
    print("=== 测试accept_both_cases装饰器修复 ===")
    
    # 1. 测试通过位置参数调用
    print("\n1. 测试位置参数调用...")
    try:
        baidu_ads_data_capture_service = BaiduAdsDataCaptureService("金蛛账户中心")
        baidu_ads_data_capture_service.oauth()
        
        # 创建报告任务
        report_task_id = baidu_ads_data_capture_service.get_ads_report_data("金蛛-新账户5", "keyword_day")
        print(f"✅ 创建报告任务成功，任务ID: {report_task_id}")
        
        # 获取任务状态 - 这里使用位置参数，测试修复后的accept_both_cases
        fetch_core = FetchAdsDataBaiduCore(baidu_ads_data_capture_service.access_token, "金蛛-新账户5")
        status_response = fetch_core.get_task_status(report_task_id)  # 位置参数调用
        print(f"✅ 通过位置参数获取任务状态成功: {status_response.get('header', {}).get('desc', 'unknown')}")
        
    except Exception as e:
        print(f"❌ 位置参数调用失败: {e}")
        raise
    
    # 2. 测试通过关键字参数调用
    print("\n2. 测试关键字参数调用...")
    try:
        status_response2 = fetch_core.get_task_status(task_id=report_task_id)  # 关键字参数调用
        print(f"✅ 通过关键字参数获取任务状态成功: {status_response2.get('header', {}).get('desc', 'unknown')}")
        
    except Exception as e:
        print(f"❌ 关键字参数调用失败: {e}")
        raise
    
    # 3. 测试小驼峰格式参数调用
    print("\n3. 测试小驼峰格式参数调用...")
    try:
        status_response3 = fetch_core.get_task_status(taskId=report_task_id)  # 小驼峰格式
        print(f"✅ 通过小驼峰格式参数获取任务状态成功: {status_response3.get('header', {}).get('desc', 'unknown')}")
        
    except Exception as e:
        print(f"❌ 小驼峰格式参数调用失败: {e}")
        raise
    
    print("\n🎉 所有测试通过！accept_both_cases装饰器修复成功！")
    return report_task_id


if __name__ == "__main__":
    test_accept_both_cases_fix()