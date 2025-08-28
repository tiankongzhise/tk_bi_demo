import gzip
from pathlib import Path
from ..models import ReturnModel

def get_gz_file_data(file_path:Path):
    """获取.gz文件数据
    gz打开后里面是一个无后缀的文件,名称与gz文件一致
    编码格式不确定,需要尝试常见编码格式
    无后缀文件的数据格式：
    1. 第一行是表头
    2. 后续每行是数据，以\t分割
    """
    data = []
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
    zip_true = False
    for encoding in encodings:
        try:
            with gzip.open(file_path, 'rt', encoding=encoding) as f:
                for line in f:
                    data.append(line.strip())
            zip_true = True
            break
        except:
            continue
    if not zip_true:
        return ReturnModel(status='error', msg='文件编码格式错误')
    return ReturnModel(status='success',message=f'{file_path}文件获取成功', data=data)

def save_to_txt(data:list, file_path:Path):
    """将数据保存到txt文件
    数据格式：
    1. 第一行是表头
    2. 后续每行是数据，以\t分割
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in data:
            f.write(line + '\n')
    print(f'数据已保存到{file_path}')
    return file_path
