# -*- coding: utf-8 -*-

import sqlite3
import os
import json
from PyQt5.QtCore import QCoreApplication


class Database(object):
    """SQLite 数据库管理类，用于存储配置"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            # 默认数据库路径：应用程序目录下的 config.db
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(app_dir, 'config.db')
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库，创建表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get(self, key, default=None):
        """获取配置值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            try:
                # 尝试解析为 JSON
                return json.loads(result[0])
            except (json.JSONDecodeError, TypeError):
                # 如果不是 JSON，直接返回字符串
                return result[0]
        return default
    
    def set(self, key, value):
        """设置配置值"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 将值转换为 JSON 字符串存储
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value)
        
        cursor.execute('''
            INSERT OR REPLACE INTO config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value_str))
        
        conn.commit()
        conn.close()
    
    def delete(self, key):
        """删除配置项"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM config WHERE key = ?', (key,))
        
        conn.commit()
        conn.close()
    
    def get_all(self, prefix=None):
        """获取所有配置项，可选前缀过滤"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if prefix:
            cursor.execute('SELECT key, value FROM config WHERE key LIKE ?', (f'{prefix}%',))
        else:
            cursor.execute('SELECT key, value FROM config')
        
        results = {}
        for row in cursor.fetchall():
            key, value = row
            try:
                results[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                results[key] = value
        
        conn.close()
        return results

