#!/usr/bin/env python3
"""
配置管理模块
从环境变量或 .env 文件加载配置
"""
import os
from pathlib import Path

# 尝试加载 python-dotenv
try:
    from dotenv import load_dotenv
    # 加载 .env 文件
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    DOTENV_LOADED = True
except ImportError:
    DOTENV_LOADED = False
    print("⚠️  python-dotenv 未安装，将只使用系统环境变量")
    print("   安装方法: pip install python-dotenv")

class Config:
    """配置类"""

    # === API 密钥 ===
    QWEN_API_KEY = os.getenv('QWEN_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    # --- Telegram 配置 ---
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    # --------------------------

    # === Gemini 配置 ===
    GEMINI_MODEL_ID = os.getenv('GEMINI_MODEL_ID', 'models/gemini-2.5-flash')
    GEMINI_TIMEOUT = int(os.getenv('GEMINI_TIMEOUT', '300'))

    # === 可选配置 ===
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    PREDICTION_RETENTION_DAYS = int(os.getenv('PREDICTION_RETENTION_DAYS', '90'))
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '7'))

    @classmethod
    def validate(cls):
        """验证必要的配置是否存在"""
        errors = []

        if not cls.QWEN_API_KEY:
            errors.append("❌ QWEN_API_KEY 未设置")

        if not cls.GEMINI_API_KEY:
            errors.append("❌ GEMINI_API_KEY 未设置")

        # --- 新增：验证 Telegram 配置 ---
        if not cls.TELEGRAM_TOKEN:
            errors.append("❌ TELEGRAM_TOKEN 未设置")
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("❌ TELEGRAM_CHAT_ID 未设置")
        # ------------------------------

        if errors:
            print("\n配置错误:")
            for error in errors:
                print(f"  {error}")
            print("\n请设置环境变量或创建 .env 文件")
            return False

        return True

    @classmethod
    def print_config(cls, show_secrets=False):
        """打印当前配置（调试用）"""
        print("=" * 60)
        print("当前配置")
        print("=" * 60)

        if show_secrets:
            print(f"QWEN_API_KEY: {cls.QWEN_API_KEY}")
            print(f"GEMINI_API_KEY: {cls.GEMINI_API_KEY}")
            print(f"TELEGRAM_TOKEN: {cls.TELEGRAM_TOKEN}")
        else:
            print(f"QWEN_API_KEY: {'*' * 20 if cls.QWEN_API_KEY else '未设置'}")
            print(f"GEMINI_API_KEY: {'*' * 20 if cls.GEMINI_API_KEY else '未设置'}")
            print(f"TELEGRAM_TOKEN: {'*' * 20 if cls.TELEGRAM_TOKEN else '未设置'}")

        print(f"TELEGRAM_CHAT_ID: {cls.TELEGRAM_CHAT_ID}")
        print(f"GEMINI_MODEL_ID: {cls.GEMINI_MODEL_ID}")
        print(f"GEMINI_TIMEOUT: {cls.GEMINI_TIMEOUT}秒")
        print(f"DEBUG: {cls.DEBUG}")
        print(f"LOG_LEVEL: {cls.LOG_LEVEL}")
        print(f"PREDICTION_RETENTION_DAYS: {cls.PREDICTION_RETENTION_DAYS}天")
        print(f"BACKUP_RETENTION_DAYS: {cls.BACKUP_RETENTION_DAYS}天")
        print("=" * 60)

# 模块加载时验证配置
if __name__ == "__main__":
    Config.print_config()
    if Config.validate():
        print("\n✅ 配置验证通过")
    else:
        print("\n❌ 配置验证失败")
        exit(1)