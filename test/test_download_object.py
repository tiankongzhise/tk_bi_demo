import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import hashlib
import os

# 导入要测试的类
from app.kernel.baidu_http_core import BaiduHttpClient
from app.core.fetch_structure_baidu import FetchStructureBaiduCore


class TestBaiduHttpClientDownloadObject(unittest.TestCase):
    """测试BaiduHttpClient.download_object方法"""
    
    def setUp(self):
        """测试前准备"""
        self.client = BaiduHttpClient()
        self.temp_dir = tempfile.mkdtemp()
        self.test_content = b"test file content for md5 verification"
        self.expected_md5 = hashlib.md5(self.test_content).hexdigest()
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('app.kernel.baidu_http_core.BaiduHttpClient.client')
    def test_download_object_success(self, mock_client_context):
        """测试成功下载文件"""
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.test_content
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_context.__enter__.return_value = mock_client
        
        # 执行下载
        result = self.client.download_object(
            file_url="https://example.com/test_file.txt",
            download_dir=self.temp_dir
        )
        
        # 验证结果
        self.assertTrue(result['success'])
        self.assertEqual(result['file_name'], 'test_file.txt')
        self.assertEqual(result['md5'], self.expected_md5)
        self.assertIsNone(result['error'])
        
        # 验证文件确实被创建
        file_path = Path(result['file_path'])
        self.assertTrue(file_path.exists())
        
        # 验证文件内容
        with open(file_path, 'rb') as f:
            content = f.read()
        self.assertEqual(content, self.test_content)
    
    @patch('app.kernel.baidu_http_core.BaiduHttpClient.client')
    def test_download_object_md5_verification_success(self, mock_client_context):
        """测试MD5校验成功"""
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.test_content
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_context.__enter__.return_value = mock_client
        
        # 执行下载，提供正确的MD5
        result = self.client.download_object(
            file_url="https://example.com/test_file.txt",
            download_dir=self.temp_dir,
            expected_md5=self.expected_md5
        )
        
        # 验证结果
        self.assertTrue(result['success'])
        self.assertEqual(result['md5'], self.expected_md5)
    
    @patch('app.kernel.baidu_http_core.BaiduHttpClient.client')
    def test_download_object_md5_verification_failure(self, mock_client_context):
        """测试MD5校验失败"""
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.test_content
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_context.__enter__.return_value = mock_client
        
        # 执行下载，提供错误的MD5
        wrong_md5 = "wrong_md5_hash"
        result = self.client.download_object(
            file_url="https://example.com/test_file.txt",
            download_dir=self.temp_dir,
            expected_md5=wrong_md5,
            max_retries=1  # 减少重试次数以加快测试
        )
        
        # 验证结果
        self.assertFalse(result['success'])
        self.assertIn('MD5校验失败', result['error'])
        self.assertEqual(result['md5'], self.expected_md5)
    
    @patch('app.kernel.baidu_http_core.BaiduHttpClient.client')
    def test_download_object_http_error(self, mock_client_context):
        """测试HTTP错误"""
        # 模拟HTTP错误响应
        mock_response = Mock()
        mock_response.status_code = 404
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_context.__enter__.return_value = mock_client
        
        # 执行下载
        result = self.client.download_object(
            file_url="https://example.com/not_found.txt",
            download_dir=self.temp_dir,
            max_retries=1
        )
        
        # 验证结果
        self.assertFalse(result['success'])
        self.assertIn('HTTP错误: 404', result['error'])
    
    def test_download_object_invalid_url_filename(self):
        """测试无效URL文件名处理"""
        with patch('app.kernel.baidu_http_core.BaiduHttpClient.client') as mock_client_context:
            # 模拟HTTP响应
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = self.test_content
            
            mock_client = Mock()
            mock_client.get.return_value = mock_response
            mock_client_context.__enter__.return_value = mock_client
            
            # 执行下载，使用无文件名的URL
            result = self.client.download_object(
                file_url="https://example.com/",
                download_dir=self.temp_dir
            )
            
            # 验证结果
            self.assertTrue(result['success'])
            # 文件名应该是生成的时间戳格式
            self.assertTrue(result['file_name'].startswith('download_'))
            self.assertTrue(result['file_name'].endswith('.txt'))


class TestFetchStructureBaiduCoreDownloadObject(unittest.TestCase):
    """测试FetchStructureBaiduCore.download_object方法"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.core = FetchStructureBaiduCore(
            access_token="test_token",
            user_name="test_user",
            temp_dir=self.temp_dir
        )
        self.test_content = b"test file content"
        self.expected_md5 = hashlib.md5(self.test_content).hexdigest()
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('app.core.fetch_structure_baidu.logger')
    def test_download_object_success(self, mock_logger):
        """测试成功下载文件"""
        # 模拟BaiduHttpClient.download_object的返回值
        mock_result = {
            'success': True,
            'file_path': str(Path(self.temp_dir) / 'original_file.txt'),
            'file_name': 'original_file.txt',
            'md5': self.expected_md5,
            'error': None
        }
        
        with patch.object(self.core.http_client, 'download_object', return_value=mock_result):
            # 执行下载
            result = self.core.download_object(
                file_url="https://example.com/test_file.txt",
                expected_md5=self.expected_md5
            )
            
            # 验证结果
            self.assertTrue(result['success'])
            self.assertEqual(result['account'], 'test_user')
            self.assertIn('test_user', result['file_name'])  # 文件名应包含用户名
            self.assertEqual(result['md5'], self.expected_md5)
            
            # 验证日志记录
            mock_logger.info_core.assert_called()
    
    @patch('app.core.fetch_structure_baidu.logger')
    def test_download_object_custom_filename(self, mock_logger):
        """测试自定义文件名"""
        # 模拟BaiduHttpClient.download_object的返回值
        mock_result = {
            'success': True,
            'file_path': str(Path(self.temp_dir) / 'custom_file.txt'),
            'file_name': 'custom_file.txt',
            'md5': self.expected_md5,
            'error': None
        }
        
        with patch.object(self.core.http_client, 'download_object', return_value=mock_result):
            # 执行下载，使用自定义文件名
            result = self.core.download_object(
                file_url="https://example.com/test_file.txt",
                custom_filename="my_custom_file.txt"
            )
            
            # 验证结果
            self.assertTrue(result['success'])
            self.assertEqual(result['account'], 'test_user')
    
    @patch('app.core.fetch_structure_baidu.logger')
    def test_download_object_failure(self, mock_logger):
        """测试下载失败"""
        # 模拟BaiduHttpClient.download_object的返回值
        mock_result = {
            'success': False,
            'file_path': str(Path(self.temp_dir) / 'failed_file.txt'),
            'file_name': 'failed_file.txt',
            'md5': None,
            'error': 'HTTP错误: 404'
        }
        
        with patch.object(self.core.http_client, 'download_object', return_value=mock_result):
            # 执行下载
            result = self.core.download_object(
                file_url="https://example.com/not_found.txt"
            )
            
            # 验证结果
            self.assertFalse(result['success'])
            self.assertEqual(result['account'], 'test_user')
            self.assertIn('HTTP错误: 404', result['error'])
            
            # 验证错误日志记录
            mock_logger.error.assert_called()
    
    @patch('app.core.fetch_structure_baidu.logger')
    def test_download_object_exception(self, mock_logger):
        """测试异常处理"""
        # 模拟BaiduHttpClient.download_object抛出异常
        with patch.object(self.core.http_client, 'download_object', side_effect=Exception("网络异常")):
            # 执行下载
            result = self.core.download_object(
                file_url="https://example.com/test_file.txt"
            )
            
            # 验证结果
            self.assertFalse(result['success'])
            self.assertEqual(result['account'], 'test_user')
            self.assertIn('下载文件时发生异常', result['error'])
            self.assertIn('网络异常', result['error'])
            
            # 验证错误日志记录
            mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()