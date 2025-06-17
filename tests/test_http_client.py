from app.services.http_client import get_http_manager,HTTPClientManager,HTTPClient,HTTPConfig,RateLimiter
import unittest
from datetime import datetime
import asyncio

class TestHttpClient(unittest.TestCase):
    class_start_time:datetime|None = None
    class_end_time:datetime|None = None
    classmethod_time_dict = {}

    
    
    @classmethod
    def setUpClass(cls):
        cls.class_start_time = datetime.now()
        print(f'{cls.class_start_time}:{cls.__name__}开始执行测试')
    
    @classmethod
    def tearDownClass(cls):
        cls.class_end_time = datetime.now()
        cost_time = cls.class_end_time - cls.class_start_time
        print(f'{cls.class_end_time}:{cls.__name__}测试执行完成,总耗时:{cost_time.total_seconds()}')
        [print(f'{k}方法耗时:{(v["end_time"]-v["start_time"]).total_seconds()}')  for k,v in cls.classmethod_time_dict.items()]
    
    def setUp(self) -> None:
        start_time = datetime.now()
        method_name = self.id().split('.')[-1]  # 获取当前测试方法名
        print(f'{start_time}:{method_name}方法开始执行')
        self.classmethod_time_dict[method_name] = {}
        self.classmethod_time_dict[method_name]["start_time"] = start_time
    def tearDown(self) -> None:
        end_time = datetime.now()
        method_name = self.id().split('.')[-1]  # 获取当前测试方法名
        print(f'{end_time}:{method_name}方法执行完成')
        self.classmethod_time_dict[method_name]["end_time"] = end_time
    
    
    def test_get_http_manager(self):
        manager = get_http_manager()
        self.assertIsInstance(manager, HTTPClientManager)
        
    def test_create_http_client(self):
        manager = get_http_manager()
        config = HTTPConfig()
        rate_limiter = 10
        client = manager.create_client('test_client',config,rate_limiter)
        self.assertIsInstance(client, HTTPClient)
        self.assertIsInstance(client.config,HTTPConfig)
        self.assertEqual(client.config, config)
        self.assertIsInstance(client.rate_limiter,RateLimiter)
        self.assertEqual(client.rate_limiter, RateLimiter(rate_limiter))
    
    def test_http_client_start(self):
        manager = get_http_manager()
        config = HTTPConfig()
        rate_limiter = 10
        client = manager.create_client('test_client',config,rate_limiter)
        asyncio.run(client.start()) 
        self.assertIsNotNone(client.session)

    def test_http_manager_get(self):
        manager = get_http_manager()
        config = HTTPConfig()
        rate_limiter = 10
        client = manager.create_client('test_client',config,rate_limiter)
        asyncio.run(client.start()) 
        get_client = manager.get_client('test_client')
        self.assertIsInstance(get_client,HTTPClient)
        self.assertEqual(get_client,client)
    
    def test_http_manager_close(self):
        t_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(t_loop)
        manager = get_http_manager()
        config = HTTPConfig()
        rate_limiter = 10
        client = manager.create_client('test_client',config,rate_limiter)
        t_loop.run_until_complete(client.start()) 
        get_client = manager.get_client('test_client')
        self.assertIsInstance(get_client,HTTPClient)
        self.assertEqual(get_client,client)
        t_loop.run_until_complete(manager.close_all())
        self.assertEqual(manager._clients,{})
    
    def test_http_client_get(self):
        t_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(t_loop)
        async def _test():
            manager = get_http_manager()
            config = HTTPConfig()
            rate_limiter = 10
            client = manager.create_client('test_client',config,rate_limiter)
            await client.start()
            rsp = await client.get('https://www.baidu.com')
            print(f'------rsp:{rsp}----------')
            return rsp
        result = t_loop.run_until_complete(_test())
        self.assertIsInstance(result,dict)
        t_loop.close()
    
    def test_http_client_post(self):
        t_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(t_loop)
        async def _test():
            manager = get_http_manager()
            config = HTTPConfig()
            rate_limiter = 10
            client = manager.create_client('test_client',config,rate_limiter)
            await client.start()
            rsp = await client.post('https://www.baidu.com/s',json_data={'wd':'python'})
            print(f'------rsp:{rsp}----------')
            return rsp
        result = t_loop.run_until_complete(_test())
        self.assertIsInstance(result,dict)
        t_loop.close()

        
        
    

        





