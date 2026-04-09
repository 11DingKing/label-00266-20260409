"""
关键词业务逻辑（共享层）
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError

from app.models.keyword import Keyword

logger = logging.getLogger(__name__)


class KeywordBusinessLogic:
    """关键词业务逻辑（共享层）"""
    
    @staticmethod
    def create(db, keywords: List[str]) -> Dict[str, Any]:
        """
        创建关键词（支持批量）
        
        Args:
            db: 数据库会话
            keywords: 关键词列表
            
        Returns:
            创建结果统计
        """
        created = 0
        skipped = 0
        errors = []
        
        for keyword in keywords:
            keyword = keyword.strip()
            if not keyword:
                continue
            
            try:
                existing = db.query(Keyword).filter(
                    Keyword.keyword == keyword
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                kw = Keyword(keyword=keyword)
                db.add(kw)
                created += 1
                logger.info(f"已添加关键词: {keyword}")
            except IntegrityError:
                db.rollback()
                skipped += 1
            except Exception as e:
                error_msg = f"添加关键词失败 {keyword}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        db.commit()
        
        return {
            "created": created,
            "skipped": skipped,
            "errors": errors
        }
    
    @staticmethod
    def get_list(db, skip: int = 0, limit: int = 100) -> List[Keyword]:
        """获取关键词列表"""
        return db.query(Keyword).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db, keyword_id: int) -> Optional[Keyword]:
        """根据ID获取关键词"""
        return db.query(Keyword).filter(Keyword.id == keyword_id).first()
    
    @staticmethod
    def delete(db, keyword_id: int) -> bool:
        """删除关键词"""
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword:
            db.delete(keyword)
            db.commit()
            logger.info(f"已删除关键词: {keyword_id}")
            return True
        return False
    
    @staticmethod
    def update(db, keyword_id: int, new_keyword: str) -> Optional[Keyword]:
        """更新关键词"""
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if keyword:
            keyword.keyword = new_keyword.strip()
            db.commit()
            logger.info(f"已更新关键词: {keyword_id}")
            return keyword
        return None
    
    @staticmethod
    def get_all_keywords(db) -> List[str]:
        """获取所有关键词（用于文章生成）"""
        keywords = db.query(Keyword).all()
        return [kw.keyword for kw in keywords]
