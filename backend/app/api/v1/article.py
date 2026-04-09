"""
文章管理API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.core.database import get_db
from app.services.article_service import ArticleService
from app.services.generation_task import start_generation_task, get_task_status, cancel_task
from app.core.exceptions import APIException

router = APIRouter()


class GenerateArticlesRequest(BaseModel):
    count: int
    keyword_ids: Optional[List[int]] = None
    use_knowledge_base: bool = True
    mock: bool = False


class UpdateGenerationConfigRequest(BaseModel):
    count: int  # 每次生成文章数量
    publish_count: int = 1  # 每次定时发布文章数量（流量控制，默认1篇实现"细水长流"）
    frequency_unit: str  # minute/hour/day 发布频率单位
    frequency_value: int  # 发布频率值


class UpdateArticleRequest(BaseModel):
    title: str
    content: str


# 静态路由必须放在动态路由前面

@router.post("/generate")
async def generate_articles(
    request: GenerateArticlesRequest,
    db: Session = Depends(get_db)
):
    """异步生成文章"""
    if request.count <= 0:
        raise HTTPException(status_code=400, detail="生成数量必须大于0")
    
    # 前置校验：检查是否有关键词或知识库内容
    from app.services.keyword_service import KeywordService
    from app.services.knowledge_base_service import KnowledgeBaseService
    
    keywords = KeywordService.get_all_keywords(db)
    has_knowledge_base = False
    if request.use_knowledge_base:
        kb_content = KnowledgeBaseService.get_all_content(db)
        has_knowledge_base = bool(kb_content and kb_content.strip())
    
    if not keywords and not has_knowledge_base:
        raise HTTPException(
            status_code=400, 
            detail="请先添加关键词或上传知识库文件，至少需要其中一项才能生成文章"
        )
    
    result = start_generation_task(
        request.count,
        request.keyword_ids,
        request.use_knowledge_base
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {"success": True, "message": "生成任务已启动", "task_id": result["task_id"]}


@router.get("/generate/status")
async def get_generation_status():
    """获取生成任务状态"""
    return {"success": True, "data": get_task_status()}


@router.post("/generate/cancel")
async def cancel_generation():
    """取消生成任务"""
    result = cancel_task()
    return result


@router.post("/generate-sync")
async def generate_articles_sync(
    request: GenerateArticlesRequest,
    db: Session = Depends(get_db)
):
    """同步生成文章（旧接口，保留兼容）"""
    if request.count <= 0:
        raise HTTPException(status_code=400, detail="生成数量必须大于0")
    
    try:
        result = ArticleService.generate_articles(
            db,
            request.count,
            request.keyword_ids,
            request.use_knowledge_base,
            request.mock
        )
        
        # 如果全部失败，返回错误
        if result['generated'] == 0 and result['errors']:
            raise HTTPException(
                status_code=500, 
                detail=result['errors'][0] if result['errors'] else "生成失败"
            )
        
        return {
            "success": True,
            "message": f"成功生成 {result['generated']} 篇文章",
            "data": result
        }
    except APIException as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/generation-config")
async def get_generation_config(
    db: Session = Depends(get_db)
):
    """获取生成配置"""
    config = ArticleService.get_generation_config(db)
    return {
        "success": True,
        "data": config
    }


@router.put("/generation-config")
async def update_generation_config(
    request: UpdateGenerationConfigRequest,
    db: Session = Depends(get_db)
):
    """
    更新生成配置
    
    - count: 每次生成文章数量（如50篇）
    - publish_count: 每次定时发布数量（如1篇，实现"细水长流"）
    - frequency_unit/value: 发布频率（如每1天）
    
    示例场景：生成50篇，每天发布1篇，持续50天
    """
    if request.count <= 0:
        raise HTTPException(status_code=400, detail="生成数量必须大于0")
    
    if request.publish_count <= 0:
        raise HTTPException(status_code=400, detail="每次发布数量必须大于0")
    
    if request.frequency_unit not in ["minute", "hour", "day"]:
        raise HTTPException(status_code=400, detail="频率单位必须是 minute/hour/day")
    
    if request.frequency_value <= 0:
        raise HTTPException(status_code=400, detail="频率值必须大于0")
    
    ArticleService.update_generation_config(
        db,
        request.count,
        request.publish_count,
        request.frequency_unit,
        request.frequency_value
    )
    
    return {
        "success": True,
        "message": "配置更新成功"
    }


@router.post("/publish-all")
async def publish_all_articles(
    db: Session = Depends(get_db)
):
    """一键发布所有待发布文章"""
    result = ArticleService.publish_all(db)
    return {
        "success": True,
        "message": f"发布完成：成功 {result['published']} 篇，失败 {result['failed']} 篇",
        "data": result
    }


@router.post("/scheduled-publish/start")
async def start_scheduled_publish(
    db: Session = Depends(get_db)
):
    """启动定时发布"""
    result = ArticleService.start_scheduled_publish(db)
    return result


@router.post("/scheduled-publish/stop")
async def stop_scheduled_publish():
    """停止定时发布"""
    result = ArticleService.stop_scheduled_publish()
    return result


@router.get("/scheduled-publish/status")
async def get_scheduled_publish_status():
    """获取定时发布状态"""
    status = ArticleService.get_scheduled_publish_status()
    return {"success": True, "data": status}


@router.get("")
async def get_article_list(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取文章列表"""
    result = ArticleService.get_list(db, skip, limit, status)
    articles = result["items"]
    
    # 获取各状态统计
    stats = ArticleService.get_stats(db)
    
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": article.id,
                    "title": article.title,
                    "content_preview": article.content[:200] + "..." if len(article.content) > 200 else article.content,
                    "status": article.status,
                    "generated_at": article.generated_at.isoformat() if article.generated_at else None,
                    "published_at": article.published_at.isoformat() if article.published_at else None
                }
                for article in articles
            ],
            "total": result["total"],
            "stats": stats
        }
    }


# 动态路由放在后面

@router.get("/{article_id}")
async def get_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """获取文章详情"""
    article = ArticleService.get_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    return {
        "success": True,
        "data": {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "status": article.status,
            "generated_at": article.generated_at.isoformat() if article.generated_at else None,
            "published_at": article.published_at.isoformat() if article.published_at else None
        }
    }


@router.post("/{article_id}/publish")
async def publish_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """发布单篇文章"""
    try:
        result = ArticleService.publish_article(db, article_id)
        return {
            "success": True,
            "message": "发布成功",
            "data": result
        }
    except APIException as e:
        raise HTTPException(status_code=e.code, detail=e.message)


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    db: Session = Depends(get_db)
):
    """删除文章"""
    success = ArticleService.delete_article(db, article_id)
    if not success:
        raise HTTPException(status_code=404, detail="文章不存在")
    return {"success": True, "message": "删除成功"}


@router.put("/{article_id}")
async def update_article(
    article_id: int,
    request: UpdateArticleRequest,
    db: Session = Depends(get_db)
):
    """更新文章"""
    article = ArticleService.update_article(db, article_id, request.title, request.content)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return {
        "success": True,
        "message": "更新成功",
        "data": {
            "id": article.id,
            "title": article.title
        }
    }
