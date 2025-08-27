#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发下载功能测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tempfile
import shutil
from pathlib import Path
import hashlib
import time
from unittest.mock import Mock, patch

from app.core.fetch_structure_baidu import FetchStructureBaiduCore


def test_concurrent_download_basic():
    """测试并发下载基本功能"""
    print("测试并发下载基本功能...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        core = FetchStructureBaiduCore(
            access_token="test_token",
            user_name="test_user",
            temp_dir=temp_dir
        )
        
        # 测试空文件字典
        result = core.download_objects({})
        assert result['total_count'] == 0, "空字典处理错误"
        assert result['success_count'] == 0, "成功计数错误"
        assert result['failed_count'] == 0, "失败计数错误"
        print("✓ 空文件字典处理正确")
        
        # 测试方法签名
        import inspect
        sig = inspect.signature(core.download_objects)
        params = list(sig.parameters.keys())
        assert 'file_path_dict' in params, "缺少file_path_dict参数"
        assert 'max_workers' in params, "缺少max_workers参数"
        print("✓ download_objects方法签名正确")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("并发下载基本功能测试通过\n")


def test_concurrent_download_mock():
    """测试并发下载模拟功能"""
    print("测试并发下载模拟功能...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        core = FetchStructureBaiduCore(
            access_token="test_token",
            user_name="test_user",
            temp_dir=temp_dir
        )
        
        # 模拟文件数据
        file_path_dict = {
            'file1': {
                'url': 'https://example.com/file1.txt',
                'md5': 'mock_md5_1'
            },
            'file2': {
                'url': 'https://example.com/file2.txt',
                'md5': 'mock_md5_2'
            },
            'file3': {
                'url': 'https://example.com/file3.txt',
                'md5': 'mock_md5_3'
            }
        }
        
        # 模拟download_object方法的返回值
        def mock_download_object(file_url, expected_md5=None, custom_filename=None):
            # 模拟成功下载
            file_path = Path(temp_dir) / (custom_filename or 'mock_file.txt')
            return {
                'success': True,
                'file_path': str(file_path),
                'file_name': custom_filename or 'mock_file.txt',
                'md5': expected_md5 or 'mock_md5',
                'error': None,
                'account': 'test_user'
            }
        
        # 使用mock替换download_object方法
        with patch.object(core, 'download_object', side_effect=mock_download_object):
            result = core.download_objects(file_path_dict, max_workers=2)
            
            # 验证结果
            assert result['total_count'] == 3, f"总数错误: 期望3, 实际{result['total_count']}"
            assert result['success_count'] == 3, f"成功数错误: 期望3, 实际{result['success_count']}"
            assert result['failed_count'] == 0, f"失败数错误: 期望0, 实际{result['failed_count']}"
            assert len(result['results']) == 3, "结果数量错误"
            assert len(result['success_files']) == 3, "成功文件数量错误"
            assert len(result['failed_files']) == 0, "失败文件数量错误"
            
            print("✓ 并发下载成功场景测试通过")
            
            # 验证所有文件都被处理
            for file_id in file_path_dict.keys():
                assert file_id in result['results'], f"文件{file_id}未在结果中"
                assert result['results'][file_id]['success'], f"文件{file_id}下载失败"
            
            print("✓ 所有文件都被正确处理")
        
        # 测试部分失败的情况
        def mock_download_object_partial_fail(file_url, expected_md5=None, custom_filename=None):
            # file1成功，file2失败，file3成功
            if 'file2' in (custom_filename or ''):
                return {
                    'success': False,
                    'file_path': str(Path(temp_dir) / (custom_filename or 'mock_file.txt')),
                    'file_name': custom_filename or 'mock_file.txt',
                    'md5': None,
                    'error': '模拟下载失败',
                    'account': 'test_user'
                }
            else:
                file_path = Path(temp_dir) / (custom_filename or 'mock_file.txt')
                return {
                    'success': True,
                    'file_path': str(file_path),
                    'file_name': custom_filename or 'mock_file.txt',
                    'md5': expected_md5 or 'mock_md5',
                    'error': None,
                    'account': 'test_user'
                }
        
        with patch.object(core, 'download_object', side_effect=mock_download_object_partial_fail):
            result = core.download_objects(file_path_dict, max_workers=2)
            
            # 验证结果
            assert result['total_count'] == 3, "总数错误"
            assert result['success_count'] == 2, f"成功数错误: 期望2, 实际{result['success_count']}"
            assert result['failed_count'] == 1, f"失败数错误: 期望1, 实际{result['failed_count']}"
            assert len(result['success_files']) == 2, "成功文件数量错误"
            assert len(result['failed_files']) == 1, "失败文件数量错误"
            
            print("✓ 部分失败场景测试通过")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("并发下载模拟功能测试通过\n")


def test_performance_improvement():
    """测试性能提升效果"""
    print("测试性能提升效果...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        core = FetchStructureBaiduCore(
            access_token="test_token",
            user_name="test_user",
            temp_dir=temp_dir
        )
        
        # 模拟文件数据
        file_path_dict = {
            f'file{i}': {
                'url': f'https://example.com/file{i}.txt',
                'md5': f'mock_md5_{i}'
            }
            for i in range(1, 6)  # 5个文件
        }
        
        # 模拟下载延迟
        def mock_download_object_with_delay(file_url, expected_md5=None, custom_filename=None):
            time.sleep(0.1)  # 模拟100ms下载时间
            file_path = Path(temp_dir) / (custom_filename or 'mock_file.txt')
            return {
                'success': True,
                'file_path': str(file_path),
                'file_name': custom_filename or 'mock_file.txt',
                'md5': expected_md5 or 'mock_md5',
                'error': None,
                'account': 'test_user'
            }
        
        with patch.object(core, 'download_object', side_effect=mock_download_object_with_delay):
            # 测试并发下载
            start_time = time.time()
            result = core.download_objects(file_path_dict, max_workers=3)
            concurrent_time = time.time() - start_time
            
            # 验证结果
            assert result['success_count'] == 5, "并发下载结果错误"
            
            # 并发下载应该比串行下载快
            # 5个文件 * 0.1秒 = 0.5秒（串行）
            # 并发应该接近 0.5/3 ≈ 0.17秒（理论值）
            # 实际会有一些开销，但应该明显小于0.5秒
            assert concurrent_time < 0.4, f"并发下载时间过长: {concurrent_time}秒"
            
            print(f"✓ 并发下载时间: {concurrent_time:.2f}秒")
            print("✓ 性能提升效果明显")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("性能提升效果测试通过\n")


def main():
    """运行所有测试"""
    print("开始运行并发下载功能测试...\n")
    
    try:
        test_concurrent_download_basic()
        test_concurrent_download_mock()
        test_performance_improvement()
        
        print("🎉 所有并发下载功能测试通过！")
        print("\n并发下载功能包括:")
        print("- 支持多文件并发下载")
        print("- 可配置并发数量")
        print("- 线程安全的结果收集")
        print("- 详细的下载统计信息")
        print("- 性能优化和错误处理")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)