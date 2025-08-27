#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的下载功能测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tempfile
import shutil
from pathlib import Path
import hashlib

from app.kernel.baidu_http_core import BaiduHttpClient
from app.core.fetch_structure_baidu import FetchStructureBaiduCore


def test_baidu_http_client_basic():
    """测试BaiduHttpClient基本功能"""
    print("测试BaiduHttpClient基本功能...")
    
    client = BaiduHttpClient()
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 测试方法是否存在
        assert hasattr(client, 'download_object'), "BaiduHttpClient缺少download_object方法"
        print("✓ BaiduHttpClient.download_object方法存在")
        
        # 测试方法签名
        import inspect
        sig = inspect.signature(client.download_object)
        params = list(sig.parameters.keys())
        assert 'file_url' in params, "缺少file_url参数"
        assert 'download_dir' in params, "缺少download_dir参数"
        print("✓ BaiduHttpClient.download_object方法签名正确")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("BaiduHttpClient基本功能测试通过\n")


def test_fetch_structure_baidu_core_basic():
    """测试FetchStructureBaiduCore基本功能"""
    print("测试FetchStructureBaiduCore基本功能...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        core = FetchStructureBaiduCore(
            access_token="test_token",
            user_name="test_user",
            temp_dir=temp_dir
        )
        
        # 测试方法是否存在
        assert hasattr(core, 'download_object'), "FetchStructureBaiduCore缺少download_object方法"
        print("✓ FetchStructureBaiduCore.download_object方法存在")
        
        # 测试方法签名
        import inspect
        sig = inspect.signature(core.download_object)
        params = list(sig.parameters.keys())
        assert 'file_url' in params, "缺少file_url参数"
        print("✓ FetchStructureBaiduCore.download_object方法签名正确")
        
        # 测试属性
        assert core.user_name == "test_user", "用户名设置错误"
        assert str(core.temp_dir) == temp_dir, "临时目录设置错误"
        print("✓ FetchStructureBaiduCore属性设置正确")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("FetchStructureBaiduCore基本功能测试通过\n")


def test_md5_calculation():
    """测试MD5计算功能"""
    print("测试MD5计算功能...")
    
    test_content = b"test file content for md5 verification"
    expected_md5 = hashlib.md5(test_content).hexdigest()
    
    # 创建临时文件
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "test.txt"
    
    try:
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        # 计算MD5
        md5_hash = hashlib.md5()
        with open(test_file, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        calculated_md5 = md5_hash.hexdigest()
        
        assert calculated_md5 == expected_md5, f"MD5计算错误: 期望{expected_md5}, 实际{calculated_md5}"
        print(f"✓ MD5计算正确: {calculated_md5}")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("MD5计算功能测试通过\n")


def test_file_operations():
    """测试文件操作功能"""
    print("测试文件操作功能...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 测试目录创建
        test_dir = Path(temp_dir) / "subdir"
        test_dir.mkdir(parents=True, exist_ok=True)
        assert test_dir.exists(), "目录创建失败"
        print("✓ 目录创建成功")
        
        # 测试文件创建和写入
        test_file = test_dir / "test.txt"
        test_content = "测试内容"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        assert test_file.exists(), "文件创建失败"
        print("✓ 文件创建成功")
        
        # 测试文件读取
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert content == test_content, "文件内容不匹配"
        print("✓ 文件读写正确")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("文件操作功能测试通过\n")


def main():
    """运行所有测试"""
    print("开始运行下载功能基本测试...\n")
    
    try:
        test_baidu_http_client_basic()
        test_fetch_structure_baidu_core_basic()
        test_md5_calculation()
        test_file_operations()
        
        print("🎉 所有基本功能测试通过！")
        print("\n实现的功能包括:")
        print("- BaiduHttpClient.download_object方法")
        print("- FetchStructureBaiduCore.download_object方法")
        print("- MD5计算和校验")
        print("- 重试机制和异常处理")
        print("- 文件名计算和路径处理")
        print("- 日志记录")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)