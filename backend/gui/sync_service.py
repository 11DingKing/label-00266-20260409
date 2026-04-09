"""
GUI同步服务层
使用同步数据库会话，调用共享的business_logic层
"""
import logging
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from app.core.database_sync import SyncSessionLocal, get_sync_db_context, test_db_connection
from app.business_logic.article_logic import ArticleBusinessLogic
from app.business_logic.keyword_logic import KeywordBusinessLogic
from app.business_logic.knowledge_base_logic import KnowledgeBaseBusinessLogic
from app.business_logic.cms_logic import CMSBusinessLogic

logger = logging.getLogger(__name__)


class SyncService:
    """同步服务基类"""
    
    @staticmethod
    @contextmanager
    def get_db():
        """获取数据库会话"""
        with get_sync_db_context() as db:
            yield db
    
    @staticmethod
    def test_connection() -> bool:
        """测试数据库连接"""
        return test_db_connection()


class SyncArticleService(SyncService):
    """同步文章服务"""
    
    @staticmethod
    def generate_articles(
        count: int,
        keyword_ids: Optional[List[int]] = None,
        use_knowledge_base: bool = True,
        mock: bool = False
    ) -> Dict[str, Any]:
        """生成文章"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.generate_articles(
                db, count, keyword_ids, use_knowledge_base, mock
            )
    
    @staticmethod
    def get_list(skip: int = 0, limit: int = 100, status: Optional[str] = None) -> Dict[str, Any]:
        """获取文章列表"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.get_list(db, skip, limit, status)
    
    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """获取文章统计"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.get_stats(db)
    
    @staticmethod
    def get_by_id(article_id: int) -> Optional[Any]:
        """根据ID获取文章"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.get_by_id(db, article_id)
    
    @staticmethod
    def publish_article(article_id: int) -> Dict[str, Any]:
        """发布单篇文章"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.publish_article(db, article_id)
    
    @staticmethod
    def publish_all() -> Dict[str, Any]:
        """一键发布所有待发布文章"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.publish_all(db)
    
    @staticmethod
    def get_generation_config() -> Dict[str, Any]:
        """获取生成配置"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.get_generation_config(db)
    
    @staticmethod
    def update_generation_config(
        count: int,
        publish_count: int,
        frequency_unit: str,
        frequency_value: int
    ):
        """更新生成配置"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.update_generation_config(
                db, count, publish_count, frequency_unit, frequency_value
            )
    
    @staticmethod
    def delete_article(article_id: int) -> bool:
        """删除文章"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.delete_article(db, article_id)
    
    @staticmethod
    def update_article(article_id: int, title: str, content: str) -> Optional[Any]:
        """更新文章"""
        with SyncArticleService.get_db() as db:
            return ArticleBusinessLogic.update_article(db, article_id, title, content)


class SyncKeywordService(SyncService):
    """同步关键词服务"""
    
    @staticmethod
    def create(keywords: List[str]) -> Dict[str, Any]:
        """创建关键词"""
        with SyncKeywordService.get_db() as db:
            return KeywordBusinessLogic.create(db, keywords)
    
    @staticmethod
    def get_list(skip: int = 0, limit: int = 100) -> List[Any]:
        """获取关键词列表"""
        with SyncKeywordService.get_db() as db:
            return KeywordBusinessLogic.get_list(db, skip, limit)
    
    @staticmethod
    def get_by_id(keyword_id: int) -> Optional[Any]:
        """根据ID获取关键词"""
        with SyncKeywordService.get_db() as db:
            return KeywordBusinessLogic.get_by_id(db, keyword_id)
    
    @staticmethod
    def delete(keyword_id: int) -> bool:
        """删除关键词"""
        with SyncKeywordService.get_db() as db:
            return KeywordBusinessLogic.delete(db, keyword_id)
    
    @staticmethod
    def update(keyword_id: int, new_keyword: str) -> Optional[Any]:
        """更新关键词"""
        with SyncKeywordService.get_db() as db:
            return KeywordBusinessLogic.update(db, keyword_id, new_keyword)
    
    @staticmethod
    def get_all_keywords() -> List[str]:
        """获取所有关键词"""
        with SyncKeywordService.get_db() as db:
            return KeywordBusinessLogic.get_all_keywords(db)


class SyncKnowledgeBaseService(SyncService):
    """同步知识库服务"""
    
    @staticmethod
    def scan_folder(folder_path: str) -> Dict[str, Any]:
        """扫描文件夹"""
        with SyncKnowledgeBaseService.get_db() as db:
            return KnowledgeBaseBusinessLogic.scan_folder(db, folder_path)
    
    @staticmethod
    def get_list(skip: int = 0, limit: int = 100) -> List[Any]:
        """获取知识库列表"""
        with SyncKnowledgeBaseService.get_db() as db:
            return KnowledgeBaseBusinessLogic.get_list(db, skip, limit)
    
    @staticmethod
    def get_list_light(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取知识库列表（轻量级）"""
        with SyncKnowledgeBaseService.get_db() as db:
            return KnowledgeBaseBusinessLogic.get_list_light(db, skip, limit)
    
    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """获取知识库统计"""
        with SyncKnowledgeBaseService.get_db() as db:
            return KnowledgeBaseBusinessLogic.get_stats(db)
    
    @staticmethod
    def get_by_id(kb_id: int) -> Optional[Any]:
        """根据ID获取知识库条目"""
        with SyncKnowledgeBaseService.get_db() as db:
            return KnowledgeBaseBusinessLogic.get_by_id(db, kb_id)
    
    @staticmethod
    def add_from_upload(filename: str, file_type: str, content: str) -> Any:
        """从上传文件添加知识库条目"""
        with SyncKnowledgeBaseService.get_db() as db:
            return KnowledgeBaseBusinessLogic.add_from_upload(db, filename, file_type, content)
    
    @staticmethod
    def delete(kb_id: int) -> bool:
        """删除知识库条目"""
        with SyncKnowledgeBaseService.get_db() as db:
            return KnowledgeBaseBusinessLogic.delete(db, kb_id)
    
    @staticmethod
    def get_all_content(max_length: int = 50000) -> str:
        """获取知识库内容摘要"""
        with SyncKnowledgeBaseService.get_db() as db:
            return KnowledgeBaseBusinessLogic.get_all_content(db, max_length)
    
    @staticmethod
    def clear_all() -> int:
        """清空所有知识库内容"""
        with SyncKnowledgeBaseService.get_db() as db:
            return KnowledgeBaseBusinessLogic.clear_all(db)


class SyncCMSService(SyncService):
    """同步CMS服务"""
    
    @staticmethod
    def get_active_config() -> Optional[Any]:
        """获取激活的CMS配置"""
        with SyncCMSService.get_db() as db:
            return CMSBusinessLogic.get_active_config(db)
    
    @staticmethod
    def get_config(config_id: int) -> Optional[Any]:
        """根据ID获取CMS配置"""
        with SyncCMSService.get_db() as db:
            return CMSBusinessLogic.get_config(db, config_id)
    
    @staticmethod
    def get_all_configs() -> List[Any]:
        """获取所有CMS配置"""
        with SyncCMSService.get_db() as db:
            return CMSBusinessLogic.get_all_configs(db)
    
    @staticmethod
    def create_config(
        platform: str,
        api_url: str,
        username: str,
        password: str,
        is_active: bool = False
    ) -> Any:
        """创建CMS配置"""
        with SyncCMSService.get_db() as db:
            return CMSBusinessLogic.create_config(
                db, platform, api_url, username, password, is_active
            )
    
    @staticmethod
    def update_config(
        config_id: int,
        platform: str = None,
        api_url: str = None,
        username: str = None,
        password: str = None,
        is_active: bool = None
    ) -> Optional[Any]:
        """更新CMS配置"""
        with SyncCMSService.get_db() as db:
            return CMSBusinessLogic.update_config(
                db, config_id, platform, api_url, username, password, is_active
            )
    
    @staticmethod
    def delete_config(config_id: int) -> bool:
        """删除CMS配置"""
        with SyncCMSService.get_db() as db:
            return CMSBusinessLogic.delete_config(db, config_id)
    
    @staticmethod
    def test_connection(config_id: int) -> bool:
        """测试CMS连接"""
        with SyncCMSService.get_db() as db:
            return CMSBusinessLogic.test_connection(db, config_id)
    
    @staticmethod
    def test_connection_direct(
        platform: str,
        api_url: str,
        username: str = None,
        password: str = None
    ) -> bool:
        """测试CMS连接（直接提供凭据）"""
        return CMSBusinessLogic.test_connection_direct(platform, api_url, username, password)
