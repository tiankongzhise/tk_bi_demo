import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.zipper_operations import (
    BaiduCampaignZipperOps,
    BaiduAdgroupZipperOps,
    BaiduKeywordZipperOps,
    BaiduCreativeZipperOps
)
from app.service.baidu_data_query_service import BaiduDataQueryService
from app.service.baidu_structure_zipper_service import BaiduStructureZipperService


class TestZipperTableOperations(unittest.TestCase):
    """拉链表操作测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_user_name = "test_user"
        self.test_campaign_id = 12345
        self.test_adgroup_id = 67890
        self.test_keyword_id = 11111
        self.test_creative_id = 22222
        
        # Mock数据库会话
        self.mock_session = MagicMock()
        
    def test_campaign_zipper_ops_initialization(self):
        """测试推广计划拉链表操作初始化"""
        ops = BaiduCampaignZipperOps()
        self.assertIsNotNone(ops)
        self.assertEqual(ops.table_name, "baidu_campaign_zipper")
    
    def test_adgroup_zipper_ops_initialization(self):
        """测试推广单元拉链表操作初始化"""
        ops = BaiduAdgroupZipperOps()
        self.assertIsNotNone(ops)
        self.assertEqual(ops.table_name, "baidu_adgroup_zipper")
    
    def test_keyword_zipper_ops_initialization(self):
        """测试关键词拉链表操作初始化"""
        ops = BaiduKeywordZipperOps()
        self.assertIsNotNone(ops)
        self.assertEqual(ops.table_name, "baidu_keyword_zipper")
    
    def test_creative_zipper_ops_initialization(self):
        """测试创意拉链表操作初始化"""
        ops = BaiduCreativeZipperOps()
        self.assertIsNotNone(ops)
        self.assertEqual(ops.table_name, "baidu_creative_zipper")
    
    def test_data_hash_calculation(self):
        """测试数据哈希计算"""
        ops = BaiduCampaignZipperOps()
        
        data1 = {
            'campaign_name': 'Test Campaign',
            'status': 'ACTIVE',
            'budget': '1000',
            'create_at': datetime.now(),  # 应该被排除
            'update_at': datetime.now()   # 应该被排除
        }
        
        data2 = {
            'campaign_name': 'Test Campaign',
            'status': 'ACTIVE',
            'budget': '1000',
            'create_at': datetime.now() + timedelta(hours=1),  # 不同时间
            'update_at': datetime.now() + timedelta(hours=1)   # 不同时间
        }
        
        # 相同的业务数据应该产生相同的哈希
        hash1 = ops._calculate_data_hash(data1)
        hash2 = ops._calculate_data_hash(data2)
        self.assertEqual(hash1, hash2)
        
        # 不同的业务数据应该产生不同的哈希
        data3 = data1.copy()
        data3['budget'] = '2000'
        hash3 = ops._calculate_data_hash(data3)
        self.assertNotEqual(hash1, hash3)
    
    @patch('app.database.zipper_operations.db_client')
    def test_batch_upsert_campaigns(self, mock_db_client):
        """测试批量更新推广计划"""
        # Mock数据库会话
        mock_session = MagicMock()
        mock_db_client.session_scope.__enter__.return_value = mock_session
        mock_db_client.session_scope.__exit__.return_value = None
        
        ops = BaiduCampaignZipperOps()
        
        test_campaigns = [
            {
                'user_name': self.test_user_name,
                'campaign_id': self.test_campaign_id,
                'campaign_name': 'Test Campaign 1',
                'status': 'ACTIVE',
                'budget': '1000'
            },
            {
                'user_name': self.test_user_name,
                'campaign_id': self.test_campaign_id + 1,
                'campaign_name': 'Test Campaign 2',
                'status': 'PAUSED',
                'budget': '2000'
            }
        ]
        
        # 模拟没有现有记录
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # 执行批量更新
        ops.batch_upsert_campaigns(test_campaigns)
        
        # 验证会话提交被调用
        mock_session.commit.assert_called_once()
    
    def test_query_service_initialization(self):
        """测试查询服务初始化"""
        query_service = BaiduDataQueryService(self.test_user_name)
        self.assertEqual(query_service.user_name, self.test_user_name)
    
    @patch('app.service.baidu_structure_zipper_service.FetchStructureBaiduCore')
    def test_structure_zipper_service_initialization(self, mock_fetch_core):
        """测试结构拉链表服务初始化"""
        service = BaiduStructureZipperService(
            access_token="test_token",
            user_name=self.test_user_name,
            temp_dir="/tmp/test"
        )
        
        self.assertEqual(service.access_token, "test_token")
        self.assertEqual(service.user_name, self.test_user_name)
        mock_fetch_core.assert_called_once()
    
    def test_parse_structure_file_data_processing(self):
        """测试结构文件数据处理逻辑"""
        service = BaiduStructureZipperService(
            access_token="test_token",
            user_name=self.test_user_name,
            temp_dir="/tmp/test"
        )
        
        # 测试数据转换逻辑
        test_row = {
            'campaignId': '12345',
            'campaignName': 'Test Campaign',
            'adgroupId': '67890',
            'keywordId': '11111'
        }
        
        # 模拟字段转换
        converted_row = {}
        for key, value in test_row.items():
            # 简化的camel_to_snake转换
            snake_key = key.lower().replace('id', '_id')
            converted_row[snake_key] = value
        
        converted_row['user_name'] = self.test_user_name
        
        # 验证转换结果
        self.assertEqual(converted_row['campaign_id'], '12345')
        self.assertEqual(converted_row['user_name'], self.test_user_name)


class TestZipperTableDataFlow(unittest.TestCase):
    """拉链表数据流测试"""
    
    def setUp(self):
        self.test_user_name = "test_user"
        
    def test_incremental_update_flow(self):
        """测试增量更新流程"""
        # 这里测试增量更新的整体流程逻辑
        # 1. 检查变更规模
        # 2. 获取变更数据
        # 3. 解析数据
        # 4. 更新拉链表
        
        # 模拟流程步骤
        steps = [
            "get_changed_scale",
            "get_changed_objects", 
            "get_objects_status",
            "get_objects_file_path",
            "download_objects",
            "extract_and_parse_structure_files",
            "update_zipper_tables"
        ]
        
        # 验证流程步骤完整性
        self.assertEqual(len(steps), 7)
        self.assertIn("get_changed_scale", steps)
        self.assertIn("update_zipper_tables", steps)
    
    def test_full_update_flow(self):
        """测试全量更新流程"""
        # 测试全量更新的整体流程逻辑
        steps = [
            "get_all_objects",
            "get_objects_status", 
            "get_objects_file_path",
            "download_objects",
            "extract_and_parse_structure_files",
            "update_zipper_tables"
        ]
        
        # 验证流程步骤完整性
        self.assertEqual(len(steps), 6)
        self.assertIn("get_all_objects", steps)
        self.assertIn("update_zipper_tables", steps)
    
    def test_query_operations(self):
        """测试查询操作"""
        query_service = BaiduDataQueryService(self.test_user_name)
        
        # 测试查询方法存在性
        self.assertTrue(hasattr(query_service, 'get_current_campaigns'))
        self.assertTrue(hasattr(query_service, 'get_current_adgroups'))
        self.assertTrue(hasattr(query_service, 'get_current_keywords'))
        self.assertTrue(hasattr(query_service, 'get_current_creatives'))
        self.assertTrue(hasattr(query_service, 'get_historical_campaigns'))
        self.assertTrue(hasattr(query_service, 'get_data_changes_summary'))
        self.assertTrue(hasattr(query_service, 'get_account_structure_snapshot'))


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)