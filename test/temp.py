
class test_a(object):
    def __init__(self,controler_name:str,controler_id:str|None = None,**kwargs):
        self.controler_name = controler_name
        self.controler_id = controler_id
        self.kwargs = kwargs
        print(f'controler_name:{controler_name},controler_id:{controler_id},kwargs:{kwargs}')


x = test_a('test_a')
