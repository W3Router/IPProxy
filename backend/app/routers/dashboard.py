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
from sqlalchemy import func, distinct
import traceback

from app.database import get_db
from app.models.dashboard import ProxyInfo
from app.core.config import settings
from app.models.instance import Instance
from app.services import ProxyService, UserService
from app.models.user import User
from app.services.auth import get_current_user
from app.services.dashboard import DashboardService
from app.models.transaction import Transaction
from app.models.product_inventory import ProductInventory
from app.models.resource_usage import ResourceUsageStatistics, ResourceUsageHistory
from app.models.dynamic_order import DynamicOrder
from app.models.static_order import StaticOrder
from app.core.deps import get_dashboard_service

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

def sync_proxy_info(db: Session):
    """同步代理信息到数据库"""
    try:
        service = IPProxyService()
        
        # 同步住宅代理信息
        residential_info = service._make_request("/api/open/app/proxy/info/v2", {
            "appUsername": settings.IPPROXY_MAIN_USERNAME,
            "username": settings.IPPROXY_MAIN_USERNAME,
            "proxyType": 1
        })
        
        # 同步数据中心代理信息
        datacenter_info = service._make_request("/api/open/app/proxy/info/v2", {
            "appUsername": settings.IPPROXY_MAIN_USERNAME,
            "username": settings.IPPROXY_MAIN_USERNAME,
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

@router.get("/open/app/dashboard/info/v2")
async def get_dashboard_info(
    db: Session = Depends(get_db),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """获取仪表盘数据"""
    try:
        logger.info("[Dashboard Service] 开始获取仪表盘数据")
        
        # 获取用户统计数据
        user_stats = await dashboard_service.get_user_statistics(current_user.id, db)
        
        # 获取每日统计数据
        daily_stats = await dashboard_service.get_daily_statistics(db)
        
        # 构造前端期望的响应格式
        response_data = {
            "code": 0,
            "msg": "success",
            "data": {
                "statistics": {
                    "balance": float(user_stats.get("balance", 0)),
                    "totalRecharge": float(user_stats.get("total_amount", 0)),
                    "totalConsumption": float(user_stats.get("total_orders", 0)),
                    "monthRecharge": float(user_stats.get("monthly_amount", 0)),
                    "monthConsumption": float(user_stats.get("monthly_orders", 0)),
                    "lastMonthConsumption": float(user_stats.get("last_month_orders", 0))
                },
                "dynamicResources": user_stats.get("dynamicResources", []),
                "staticResources": user_stats.get("staticResources", []),
                "dailyStats": daily_stats
            }
        }
        
        logger.info("[Dashboard Service] 仪表盘数据获取成功")
        logger.debug(f"[Dashboard Service] 响应数据: {response_data}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"[Dashboard Service] 获取仪表盘数据失败: {str(e)}")
        return {
            "code": 500,
            "msg": f"获取仪表盘数据失败: {str(e)}",
            "data": None
        }

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
    try:
        # 获取动态资源使用情况
        resources = []
        
        # 获取动态订单统计
        dynamic_orders = db.query(DynamicOrder).filter(
            DynamicOrder.user_id == user_id
        ).all()
        
        if dynamic_orders:
            total_usage = sum(order.total_traffic for order in dynamic_orders)
            monthly_usage = sum(order.monthly_traffic for order in dynamic_orders)
            today_usage = sum(order.today_traffic for order in dynamic_orders)
            last_month_usage = sum(order.last_month_traffic for order in dynamic_orders)
            
            resources.append({
                "id": "1",
                "name": "动态代理",
                "usageRate": float(monthly_usage / total_usage * 100 if total_usage else 0),
                "total": float(total_usage),
                "monthly": float(monthly_usage),
                "today": float(today_usage),
                "lastMonth": float(last_month_usage)
            })
        
        return resources
        
    except Exception as e:
        logger.error(f"获取动态资源使用情况失败: {str(e)}")
        return []

def get_static_resources_usage(db: Session, user_id: int) -> list:
    """获取静态资源使用情况"""
    try:
        # 获取静态资源使用情况
        resources = []
        
        # 获取静态订单统计
        static_orders = db.query(StaticOrder).filter(
            StaticOrder.user_id == user_id
        ).all()
        
        if static_orders:
            total = len(static_orders)
            available = sum(1 for order in static_orders if order.status == 'active')
            expired = sum(1 for order in static_orders if order.status == 'expired')
            
            # 获取本月和上月的开通数量
            now = datetime.now()
            start_of_month = datetime(now.year, now.month, 1)
            start_of_last_month = start_of_month - timedelta(days=start_of_month.day)
            
            monthly = sum(1 for order in static_orders 
                         if order.created_at >= start_of_month)
            last_month = sum(1 for order in static_orders 
                            if start_of_last_month <= order.created_at < start_of_month)
            
            resources.append({
                "id": "1",
                "name": "静态代理",
                "usageRate": float(available / total * 100 if total else 0),
                "total": float(total),
                "available": float(available),
                "monthly": float(monthly),
                "lastMonth": float(last_month),
                "expired": float(expired)
            })
        
        return resources
        
    except Exception as e:
        logger.error(f"获取静态资源使用情况失败: {str(e)}")
        return []

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

@router.get("/dashboard/agent/{agent_id}")
async def get_agent_dashboard(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取代理商仪表盘数据"""
    try:
        logger.info(f"[DashboardRouter] 获取代理商仪表盘: agent_id={agent_id}")
        
        # 从数据库获取代理商信息
        agent = db.query(User).filter(
            User.id == agent_id,
            User.is_agent == True
        ).first()
        
        if not agent:
            return {
                "code": 404,
                "msg": "代理商不存在",
                "data": None
            }
            
        # 获取代理商统计数据
        total_recharge = get_total_recharge(db, agent_id)
        total_consumption = get_total_consumption(db, agent_id)
        month_recharge = get_month_recharge(db, agent_id)
        month_consumption = get_month_consumption(db, agent_id)
        last_month_consumption = get_last_month_consumption(db, agent_id)
        
        # 获取资源使用情况
        dynamic_resources = get_dynamic_resources_usage(db, agent_id)
        static_resources = get_static_resources_usage(db, agent_id)
        
        response_data = {
            "agent": {
                "id": agent.id,
                "username": agent.username,
                "balance": float(agent.balance),
                "status": "active" if agent.status == 1 else "inactive",
                "created_at": agent.created_at.isoformat() if agent.created_at else None
            },
            "statistics": {
                "totalRecharge": float(total_recharge),
                "totalConsumption": float(total_consumption),
                "monthRecharge": float(month_recharge),
                "monthConsumption": float(month_consumption),
                "lastMonthConsumption": float(last_month_consumption),
                "balance": float(agent.balance)
            },
            "dynamicResources": dynamic_resources,
            "staticResources": static_resources
        }
        
        logger.info(f"[DashboardRouter] 返回代理商仪表盘数据: {json.dumps(response_data, ensure_ascii=False)}")
        
        return {
            "code": 0,
            "msg": "success",
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"[DashboardRouter] 获取代理商仪表盘失败: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "code": 500,
            "msg": f"获取代理商仪表盘失败: {str(e)}",
            "data": None
        }

@router.get("/dashboard/agent/statistics")
async def get_agent_statistics(
    agentId: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取代理商统计数据"""
    try:
        logger.info(f"[Dashboard] 开始获取代理商统计数据: agentId={agentId}")
        
        # 获取代理商信息
        agent = db.query(User).filter(
            User.id == agentId,
            User.is_agent == True
        ).first()
        
        if not agent:
            logger.error(f"[Dashboard] 代理商不存在: agentId={agentId}")
            return {
                "code": 404,
                "msg": "代理商不存在",
                "data": None
            }
            
        # 返回代理商统计数据
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "balance": float(agent.balance or 0),
                "totalUsers": len(agent.users) if agent.users else 0,
                "activeUsers": len([u for u in agent.users if u.status == 'active']) if agent.users else 0
            }
        }
        
    except Exception as e:
        logger.error(f"[Dashboard] 获取代理商统计数据失败: {str(e)}")
        return {
            "code": 500,
            "msg": f"获取代理商统计数据失败: {str(e)}",
            "data": None
        }

@router.get("/api/dashboard/resources", response_model=Dict[str, List[Dict[str, Any]]])
async def get_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """获取动态和静态资源数据"""
    try:
        logger.info(f"用户 {current_user.username} 请求获取资源数据")
        
        # 获取动态资源数据
        dynamic_resources = []
        dynamic_orders = db.query(DynamicOrder).filter(
            DynamicOrder.user_id == current_user.id,
            DynamicOrder.status == "active"
        ).all()
        
        for order in dynamic_orders:
            usage_stats = db.query(ResourceUsageStatistics).filter(
                ResourceUsageStatistics.order_id == order.id,
                ResourceUsageStatistics.resource_type == "dynamic"
            ).first()
            
            if usage_stats:
                dynamic_resources.append({
                    "title": order.resource_name,
                    "total": order.total_amount,
                    "used": usage_stats.used_amount,
                    "remaining": order.total_amount - usage_stats.used_amount,
                    "percentage": round((usage_stats.used_amount / order.total_amount) * 100, 2) if order.total_amount > 0 else 0,
                    "today_usage": usage_stats.today_usage,
                    "month_usage": usage_stats.month_usage,
                    "last_month_usage": usage_stats.last_month_usage
                })
        
        # 获取静态资源数据
        static_resources = []
        static_orders = db.query(StaticOrder).filter(
            StaticOrder.user_id == current_user.id,
            StaticOrder.status == "active"
        ).all()
        
        for order in static_orders:
            usage_stats = db.query(ResourceUsageStatistics).filter(
                ResourceUsageStatistics.order_id == order.id,
                ResourceUsageStatistics.resource_type == "static"
            ).first()
            
            if usage_stats:
                static_resources.append({
                    "title": order.resource_name,
                    "total": order.total_quantity,
                    "used": usage_stats.used_quantity,
                    "available": order.total_quantity - usage_stats.used_quantity,
                    "percentage": round((usage_stats.used_quantity / order.total_quantity) * 100, 2) if order.total_quantity > 0 else 0,
                    "month_opened": usage_stats.month_opened,
                    "last_month_opened": usage_stats.last_month_opened
                })
        
        logger.info(f"成功获取资源数据：动态资源 {len(dynamic_resources)} 个，静态资源 {len(static_resources)} 个")
        return {
            "dynamicResources": dynamic_resources,
            "staticResources": static_resources
        }
        
    except Exception as e:
        logger.error(f"获取资源数据失败: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"获取资源数据失败: {str(e)}"
        )
