"""
知识库业务逻辑（共享层）
"""
import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from app.models.knowledge_base import KnowledgeBase
from app.core.exceptions import FileReadException
from app.services.file_parser import FileParser

logger = logging.getLogger(__name__)


class KnowledgeBaseBusinessLogic:
    """知识库业务逻辑（共享层）"""
    
    @staticmethod
    def scan_folder(db, folder_path: str) -> Dict[str, Any]:
        """
        同步扫描文件夹
        
        Args:
            db: 数据库会话
            folder_path: 文件夹路径
            
        Returns:
            扫描结果统计
        """
        if not os.path.exists(folder_path):
            raise FileReadException(f"文件夹不存在: {folder_path}")
        
        if not os.path.isdir(folder_path):
            raise FileReadException(f"路径不是文件夹: {folder_path}")
        
        folder_path = os.path.abspath(folder_path)
        logger.info(f"开始扫描文件夹: {folder_path}")
        
        supported_exts = FileParser.get_supported_extensions()
        all_files = []
        
        for ext in supported_exts:
            pattern = f"*{ext}"
            all_files.extend([(f, ext[1:]) for f in Path(folder_path).rglob(pattern)])
        
        total_files = len(all_files)
        processed = 0
        skipped = 0
        errors = []
        
        for file_path, file_type in all_files:
            try:
                file_path_str = str(file_path)
                existing = db.query(KnowledgeBase).filter(
                    KnowledgeBase.file_path == file_path_str
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                content = FileParser.parse(file_path_str)
                if content:
                    kb = KnowledgeBase(
                        file_path=file_path_str,
                        file_type=file_type,
                        content=content
                    )
                    db.add(kb)
                    processed += 1
                    logger.info(f"已处理文件: {file_path_str}")
            except Exception as e:
                error_msg = f"处理文件失败 {file_path}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        db.commit()
        
        result = {
            "total_files": total_files,
            "processed": processed,
            "skipped": skipped,
            "errors": errors
        }
        
        logger.info(f"扫描完成: {result}")
        return result
    
    @staticmethod
    def get_list(db, skip: int = 0, limit: int = 100) -> List[KnowledgeBase]:
        """获取知识库列表"""
        return db.query(KnowledgeBase).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_list_light(db, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取知识库列表（轻量级，使用SQL截取内容预览）"""
        from sqlalchemy import func
        
        results = db.query(
            KnowledgeBase.id,
            KnowledgeBase.file_path,
            KnowledgeBase.file_type,
            func.substr(KnowledgeBase.content, 1, 200).label('content_preview'),
            KnowledgeBase.created_at
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "file_path": r.file_path,
                "file_type": r.file_type,
                "content_preview": (r.content_preview + "...") if r.content_preview and len(r.content_preview) >= 200 else r.content_preview,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    
    @staticmethod
    def get_stats(db) -> Dict[str, Any]:
        """获取知识库统计信息"""
        from sqlalchemy import func
        
        total = db.query(func.count(KnowledgeBase.id)).scalar() or 0
        
        type_counts = db.query(
            KnowledgeBase.file_type,
            func.count(KnowledgeBase.id)
        ).group_by(KnowledgeBase.file_type).all()
        
        stats = {"total": total, "txt": 0, "pdf": 0, "docx": 0, "xlsx": 0, "md": 0}
        for file_type, count in type_counts:
            if file_type in stats:
                stats[file_type] = count
        
        return stats
    
    @staticmethod
    def get_by_id(db, kb_id: int) -> Optional[KnowledgeBase]:
        """根据ID获取知识库条目"""
        return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    
    @staticmethod
    def get_by_filename(db, filename: str) -> Optional[KnowledgeBase]:
        """根据文件名获取知识库条目"""
        return db.query(KnowledgeBase).filter(
            KnowledgeBase.file_path.endswith(filename)
        ).first()
    
    @staticmethod
    def add_from_upload(db, filename: str, file_type: str, content: str) -> KnowledgeBase:
        """
        从上传文件添加知识库条目
        
        Args:
            db: 数据库会话
            filename: 原始文件名
            file_type: 文件类型（不含点号）
            content: 解析后的文本内容
        """
        kb = KnowledgeBase(
            file_path=f"[上传] {filename}",
            file_type=file_type,
            content=content
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        logger.info(f"已添加上传文件到知识库: {filename}")
        return kb
    
    @staticmethod
    def delete(db, kb_id: int) -> bool:
        """删除知识库条目"""
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if kb:
            db.delete(kb)
            db.commit()
            logger.info(f"已删除知识库条目: {kb_id}")
            return True
        return False
    
    @staticmethod
    def _extract_key_content(content: str, max_length: int = 3000) -> str:
        """
        智能提取文档关键内容
        """
        if not content or len(content) <= max_length:
            return content
        
        paragraphs = content.split('\n')
        result_parts = []
        current_length = 0
        
        head_budget = max_length // 3
        for para in paragraphs[:10]:
            para = para.strip()
            if not para:
                continue
            if current_length + len(para) > head_budget:
                break
            result_parts.append(para)
            current_length += len(para) + 1
        
        key_markers = ['#', '##', '###', '1.', '2.', '3.', '一、', '二、', '三、', '•', '-', '总结', '结论', '要点']
        remaining_budget = max_length - current_length
        
        for para in paragraphs[10:]:
            para = para.strip()
            if not para or para in result_parts:
                continue
            
            is_key = any(para.startswith(marker) for marker in key_markers)
            is_short = 20 < len(para) < 200
            
            if is_key or is_short:
                if current_length + len(para) > max_length:
                    break
                result_parts.append(para)
                current_length += len(para) + 1
        
        return '\n'.join(result_parts)
    
    @staticmethod
    def get_all_content(db, max_length: int = 50000) -> str:
        """
        获取知识库内容摘要（用于文章生成）
        """
        kbs = db.query(KnowledgeBase).all()
        if not kbs:
            return ""
        
        contents = []
        total_length = 0
        per_doc_budget = max(2000, max_length // max(len(kbs), 1))
        
        for kb in kbs:
            if total_length >= max_length:
                break
            
            if not kb.content:
                continue
            
            extracted = KnowledgeBaseBusinessLogic._extract_key_content(
                kb.content, 
                min(per_doc_budget, max_length - total_length)
            )
            
            if extracted:
                file_name = os.path.basename(kb.file_path)
                content_with_source = f"[来源: {file_name}]\n{extracted}"
                contents.append(content_with_source)
                total_length += len(content_with_source)
        
        result = "\n\n---\n\n".join(contents)
        return result[:max_length] if len(result) > max_length else result
    
    @staticmethod
    def clear_all(db) -> int:
        """清空所有知识库内容"""
        count = db.query(KnowledgeBase).count()
        db.query(KnowledgeBase).delete()
        db.commit()
        logger.info(f"已清空知识库，共删除 {count} 条记录")
        return count
