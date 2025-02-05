# 仪表盘路由模块
# ==============
#
# 此模块处理所有与仪表盘相关的路由请求，包括：
# - 统计数据展示（账户余额、充值消费等）
# - 动态资源监控（流量使用情况）
# - 静态资源监控（IP使用情况）
# - 实时数据同步
#
# 重要提示：
# ---------
# 1. 此模块是系统监控的核心，需要保证数据的实时性和准确性
# 2. 需要合理处理大量数据的展示和更新
# 3. 注意性能优化，避免频繁的数据库查询
#
# 依赖关系：
# ---------
# - 数据模型：
#   - ProxyInfo (app/models/dashboard.py)
#   - ResourceUsage (app/models/dashboard.py)
#   - MainUser (app/models/main_user.py)
# - 服务：
#   - IPProxyService (app/services/ipproxy_service.py)
#
# 前端对应：
# ---------
# - 服务层：src/services/dashboardService.ts
# - 页面组件：src/pages/dashboard/index.tsx
# - 类型定义：src/types/dashboard.ts
#
# 数据结构：
# ---------
# 1. 统计数据：
#    - 账户余额
#    - 总充值金额
#    - 总消费金额
#    - 月度充值金额
#    - 月度消费金额
#
# 2. 动态资源：
#    - 资源名称
#    - 使用率
#    - 总流量
#    - 已用流量
#    - 剩余流量
#
# 3. 静态资源：
#    - 资源名称
#    - 使用率
#    - 总数量
#    - 已用数量
#    - 可用数量
#
# 修改注意事项：
# ------------
# 1. 数据同步：
#    - 确保数据实时性
#    - 处理同步失败情况
#    - 避免数据不一致
#
# 2. 性能优化：
#    - 使用缓存减少查询
#    - 优化大数据量查询
#    - 合理设置更新频率
#
# 3. 错误处理：
#    - 优雅处理超时
#    - 合理的重试机制
#    - 友好的错误提示
#
# 4. 安全性：
#    - 验证数据访问权限
#    - 保护敏感信息
#    - 防止数据泄露

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import requests
import json
from datetime import datetime, timedelta
import logging
from sqlalchemy import func

from app.database import get_db
from app.models.dashboard import ProxyInfo, ResourceUsage
from app.config import settings
from app.models.instance import Instance
from app.services import ProxyService, UserService
from app.routers.instance import sync_instances
from app.models.main_user import MainUser
from app.models.user import User
from app.services.auth import get_current_user
from app.services.dashboard import get_dashboard_data, DashboardService
from app.models.transaction import Transaction
from app.models.resource_type import ResourceType
from app.models.resource_usage import ResourceUsageStatistics, ResourceUsageHistory
from app.models.dynamic_order import DynamicOrder
from app.models.static_order import StaticOrder
from app.core.deps import get_proxy_service, get_user_service

router = APIRouter()
logger = logging.getLogger(__name__)

def fetch_from_ipipv_api(endpoint: str) -> Dict[str, Any]:
    """从IPIPV API获取数据"""
    try:
        response = requests.get(f"{settings.IPIPV_API_BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data from IPIPV API: {str(e)}")

def get_proxy_info_from_db(db: Session) -> ProxyInfo:
    """从数据库获取代理信息"""
    logger.debug("从数据库获取代理信息")
    proxy_info = db.query(ProxyInfo).first()
    if not proxy_info:
        logger.error("数据库中未找到代理信息")
        raise HTTPException(status_code=404, detail="Proxy info not found in database")
    return proxy_info

def get_resource_usage_from_db(db: Session) -> tuple[List[ResourceUsage], List[ResourceUsage]]:
    """从数据库获取资源使用信息"""
    logger.debug("从数据库获取资源使用信息")
    dynamic_resources = db.query(ResourceUsage).filter_by(resource_type="dynamic").all()
    static_resources = db.query(ResourceUsage).filter_by(resource_type="static").all()
    if not dynamic_resources or not static_resources:
        logger.error("数据库中未找到资源使用数据")
        raise HTTPException(status_code=404, detail="Resource usage data not found in database")
    return dynamic_resources, static_resources

def update_proxy_balance_from_api(db: Session, proxy_info: ProxyInfo) -> ProxyInfo:
    """从API更新代理余额信息"""
    try:
        api_data = fetch_from_ipipv_api("/api/open/app/proxy/info/v2")
        if api_data.get("code") == 0:
            data = api_data.get("data", {})
            proxy_info.balance = data.get("balance", proxy_info.balance)
            proxy_info.updated_at = datetime.now()
            db.commit()
            db.refresh(proxy_info)
    except Exception as e:
        # API获取失败时继续使用数据库中的数据
        pass
    return proxy_info

def update_resource_usage_from_api(db: Session, dynamic_resources: List[ResourceUsage], 
                                 static_resources: List[ResourceUsage]) -> tuple[List[ResourceUsage], List[ResourceUsage]]:
    """从API更新资源使用信息"""
    try:
        api_data = fetch_from_ipipv_api("/api/open/app/proxy/info/v2")
        if api_data.get("code") == 0:
            data = api_data.get("data", {})
            
            # 更新动态资源
            for item in data.get("dynamic_resource", []):
                resource = next((r for r in dynamic_resources if r.title == item.get("title")), None)
                if resource:
                    resource.used = item.get("used", resource.used)
                    resource.today = item.get("today", resource.today)
                    resource.percentage = item.get("percentage", resource.percentage)
                    resource.updated_at = datetime.now()
            
            # 更新静态资源
            for item in data.get("static_resource", []):
                resource = next((r for r in static_resources if r.title == item.get("title")), None)
                if resource:
                    resource.used = item.get("used", resource.used)
                    resource.today = item.get("today", resource.today)
                    resource.available = item.get("available", resource.available)
                    resource.percentage = item.get("percentage", resource.percentage)
                    resource.updated_at = datetime.now()
            
            db.commit()
            for resource in dynamic_resources + static_resources:
                db.refresh(resource)
    except Exception as e:
        # API获取失败时继续使用数据库中的数据
        pass
    return dynamic_resources, static_resources

def sync_proxy_info(db: Session, main_user: MainUser):
    """同步代理信息到数据库"""
    try:
        service = IPProxyService()
        
        # 同步住宅代理信息
        residential_info = service._make_request("/api/open/app/proxy/info/v2", {
            "appUsername": main_user.app_username,
            "username": main_user.username,
            "proxyType": 1
        })
        
        # 同步数据中心代理信息
        datacenter_info = service._make_request("/api/open/app/proxy/info/v2", {
            "appUsername": main_user.app_username,
            "username": main_user.username,
            "proxyType": 2
        })
        
        # 更新或创建代理信息记录
        proxy_info = db.query(ProxyInfo).first()
        if not proxy_info:
            proxy_info = ProxyInfo()
            db.add(proxy_info)
        
        # 更新代理信息
        proxy_info.residential_balance = residential_info.get("balance", 0)
        proxy_info.datacenter_balance = datacenter_info.get("balance", 0)
        proxy_info.updated_at = datetime.now()
        
        db.commit()
        logger.info("代理信息同步成功")
    except Exception as e:
        logger.error(f"同步代理信息失败: {str(e)}")
        # 同步失败不抛出异常，继续使用数据库中的数据

def sync_resource_usage(db: Session, main_user: MainUser):
    """同步资源使用信息到数据库"""
    try:
        service = IPProxyService()
        
        # 获取流量使用统计
        statistics = service._make_request("/api/open/app/proxy/flow/use/log/v2", {
            "appUsername": main_user.app_username,
            "username": main_user.username,
            "proxyType": 0,
            "page": 1,
            "pageSize": 10
        })
        
        # 更新或创建资源使用记录
        resource_usage = db.query(ResourceUsage).first()
        if not resource_usage:
            resource_usage = ResourceUsage()
            db.add(resource_usage)
        
        # 更新资源使用信息
        resource_usage.monthly_usage = statistics.get("monthlyUsage", 0)
        resource_usage.daily_usage = statistics.get("dailyUsage", 0)
        resource_usage.last_month_usage = statistics.get("lastMonthUsage", 0)
        resource_usage.updated_at = datetime.now()
        
        db.commit()
        logger.info("资源使用信息同步成功")
    except Exception as e:
        logger.error(f"同步资源使用信息失败: {str(e)}")
        # 同步失败不抛出异常，继续使用数据库中的数据

@router.get("/dashboard/info/v2")
async def get_dashboard_info(
    current_user: User = Depends(get_current_user),
    proxy_service: ProxyService = Depends(get_proxy_service),
    user_service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db)
):
    """获取仪表盘信息"""
    try:
        # 获取代理信息
        proxy_info = await proxy_service.get_proxy_info()
        if not proxy_info:
            raise HTTPException(status_code=500, detail="获取代理信息失败")
            
        # 获取用户统计信息
        user_stats = await user_service.get_statistics()
        if not user_stats:
            raise HTTPException(status_code=500, detail="获取用户统计信息失败")
            
        return {
            "code": 0,
            "message": "success",
            "data": {
                "proxy_info": proxy_info,
                "statistics": user_stats
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取仪表盘信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_total_recharge(db: Session, user_id: int) -> float:
    """获取累计充值金额"""
    result = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == "recharge",
        Transaction.status == "completed"
    ).with_entities(func.sum(Transaction.amount)).scalar()
    return float(result or 0)

def get_total_consumption(db: Session, user_id: int) -> float:
    """获取累计消费金额"""
    result = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == "consumption",
        Transaction.status == "completed"
    ).with_entities(func.sum(Transaction.amount)).scalar()
    return float(result or 0)

def get_month_recharge(db: Session, user_id: int) -> float:
    """获取本月充值金额"""
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    result = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == "recharge",
        Transaction.status == "completed",
        Transaction.created_at >= start_of_month
    ).with_entities(func.sum(Transaction.amount)).scalar()
    return float(result or 0)

def get_month_consumption(db: Session, user_id: int) -> float:
    """获取本月消费金额"""
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    result = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == "consumption",
        Transaction.status == "completed",
        Transaction.created_at >= start_of_month
    ).with_entities(func.sum(Transaction.amount)).scalar()
    return float(result or 0)

def get_last_month_consumption(db: Session, user_id: int) -> float:
    """获取上月消费金额"""
    now = datetime.now()
    start_of_last_month = datetime(now.year, now.month - 1 if now.month > 1 else 12, 1)
    end_of_last_month = datetime(now.year, now.month, 1) - timedelta(days=1)
    result = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.type == "consumption",
        Transaction.status == "completed",
        Transaction.created_at >= start_of_last_month,
        Transaction.created_at <= end_of_last_month
    ).with_entities(func.sum(Transaction.amount)).scalar()
    return float(result or 0)

def get_dynamic_resources_usage(db: Session, user_id: int) -> list:
    """获取动态资源使用情况"""
    # 这里需要根据实际的数据结构来实现
    # 示例数据
    return [
        {
            "id": "1",
            "name": "动态资源1",
            "usageRate": 75,
            "total": 1000,
            "monthly": 300,
            "today": 50,
            "lastMonth": 800
        },
        {
            "id": "2",
            "name": "动态资源2",
            "usageRate": 60,
            "total": 2000,
            "monthly": 500,
            "today": 80,
            "lastMonth": 1500
        }
    ]

def get_static_resources_usage(db: Session, user_id: int) -> list:
    """获取静态资源使用情况"""
    # 这里需要根据实际的数据结构来实现
    # 示例数据
    return [
        {
            "name": "静态资源1",
            "total": 100,
            "available": 80,
            "used": 20,
            "expired": 0
        },
        {
            "name": "静态资源2",
            "total": 200,
            "available": 150,
            "used": 40,
            "expired": 10
        },
        {
            "name": "静态资源3",
            "total": 300,
            "available": 200,
            "used": 80,
            "expired": 20
        },
        {
            "name": "静态资源4",
            "total": 400,
            "available": 300,
            "used": 90,
            "expired": 10
        },
        {
            "name": "静态资源5",
            "total": 500,
            "available": 400,
            "used": 80,
            "expired": 20
        },
        {
            "name": "静态资源7",
            "total": 700,
            "available": 600,
            "used": 80,
            "expired": 20
        }
    ]

@router.get("/resource-statistics")
async def get_resource_statistics(db: Session = Depends(get_db)):
    try:
        # 获取当前月份的开始时间
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)

        # 查询所有资源类型及其统计数据
        resource_stats = []
        resource_types = db.query(ResourceType).all()

        for resource_type in resource_types:
            # 获取或创建统计记录
            stats = db.query(ResourceUsageStatistics).filter(
                ResourceUsageStatistics.resource_type_id == resource_type.id
            ).first()

            if not stats:
                stats = ResourceUsageStatistics(
                    resource_type_id=resource_type.id,
                    total_openings=0,
                    monthly_openings=0,
                    available_count=0,
                    expired_count=0
                )
                db.add(stats)

            # 更新月度开通数
            monthly_openings = db.query(func.count(ResourceUsageHistory.id)).filter(
                ResourceUsageHistory.resource_type_id == resource_type.id,
                ResourceUsageHistory.created_at >= start_of_month
            ).scalar()

            # 更新可用和过期资源数
            active_count = db.query(func.count(ResourceUsageHistory.id)).filter(
                ResourceUsageHistory.resource_type_id == resource_type.id,
                ResourceUsageHistory.status == 'active'
            ).scalar()

            expired_count = db.query(func.count(ResourceUsageHistory.id)).filter(
                ResourceUsageHistory.resource_type_id == resource_type.id,
                ResourceUsageHistory.status == 'expired'
            ).scalar()

            # 更新统计数据
            stats.monthly_openings = monthly_openings
            stats.available_count = active_count
            stats.expired_count = expired_count
            stats.total_openings = active_count + expired_count

            resource_stats.append({
                'resource_type': resource_type.to_dict(),
                'statistics': stats.to_dict()
            })

        db.commit()

        return {
            'success': True,
            'data': resource_stats
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
