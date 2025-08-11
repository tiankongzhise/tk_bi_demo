#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的download_file方法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.baidu_http_core import BaiduHttpClient
from pathlib import Path

def test_download_fix():
    """测试下载文件修复"""
    
    # 创建客户端实例
    client = BaiduHttpClient()
    
    # 测试参数
    test_file_url = "https://example.com/test.txt"  # 替换为实际的文件URL
    test_headers = ["date", "MarkerContentD", "userName", "campaignNameStatus", "campaignId", "wInfoNameStatus", "wInfoId", "impression", "click", "cost", "ctr", "cpc", "qualityEnum"]
    test_data_start_row = 2
    test_file_path = Path("temp/test_download_fixed.txt")
    
    try:
        print("开始测试修复后的download_file方法...")
        print(f"文件URL: {test_file_url}")
        print(f"保存路径: {test_file_path}")
        print(f"数据起始行: {test_data_start_row}")
        print(f"自定义表头: {test_headers}")
        
        # 调用修复后的方法
        result = client.download_file(
            file_url=test_file_url,
            table_header=test_headers,
            data_start_row=test_data_start_row,
            file_path=test_file_path
        )
        
        if result:
            print("✅ 文件下载成功！")
            print(f"文件已保存到: {test_file_path.absolute()}")
            
            # 检查文件内容
            if test_file_path.exists():
                with open(test_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"文件大小: {len(content)} 字符")
                    print("文件前几行内容:")
                    lines = content.split('\n')[:5]
                    for i, line in enumerate(lines, 1):
                        print(f"  {i}: {line}")
        else:
            print("❌ 文件下载失败")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 50)
    print("百度HTTP客户端下载文件修复测试")
    print("=" * 50)
    
    print("\n修复内容:")
    print("1. 使用httpx原生客户端替代self.client，避免403错误")
    print("2. 添加完整的浏览器请求头")
    print("3. 支持多种中文编码自动检测(utf-8, gbk, gb2312, gb18030, big5)")
    print("4. 保存为制表符分隔的.txt文件，避免CSV格式问题")
    print("5. 保持原始数据格式，避免逗号分隔符导致的数据截断")
    
    print("\n注意: 请将test_file_url替换为实际的文件下载链接进行测试")
    print("\n开始测试...\n")
    
    test_download_fix()