#!/usr/bin/env python3
"""TK BI Demo 主启动文件

这是项目的主入口点，用于启动整个应用。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入应用主函数
from app.main import main

if __name__ == "__main__":
    # 设置环境变量
    os.environ.setdefault('PYTHONPATH', str(project_root))
    
    # 启动应用
    main()