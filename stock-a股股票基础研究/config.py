"""
stock-research-group 全局配置

所有模块应从此处导入 DB_PATH，避免硬编码数据库路径。
如需更改数据库位置，只需修改此文件。
"""

from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent

# 数据库路径（本地项目目录）
DB_PATH = Path("/Volumes/固态 1t/openclaw-data/finance.db")
