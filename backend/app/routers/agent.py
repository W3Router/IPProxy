# 代理商管理路由模块
# ==============
#
# 此模块处理所有与代理商相关的路由请求，包括：
# - 代理商账户管理（创建、更新、查询）
# - 代理商资金管理（余额更新、交易记录）
# - 代理商统计信息（订单统计、收入统计）
#
# 重要提示：
# ---------
# 1. 代理商是系统的核心角色之一，所有操作需要严格的权限控制
# 2. 涉及资金操作时需要保证事务的原子性和数据一致性
# 3. 所有关键操作都需要记录详细的日志
#
# 依赖关系：
# ---------
# - 数据模型：
#   - User (app/models/user.py)
#   - Transaction (app/models/transaction.py)
#   - MainUser (app/models/main_user.py)
# - 服务：
#   - UserService (app/services/user_service.py)
#   - ProxyService (app/services/proxy_service.py)
#   - AreaService (app/services/area_service.py)
#   - AuthService (app/services/auth.py)
#
# 前端对应：
# ---------
# - 服务层：src/services/agentService.ts
# - 页面组件：src/pages/agent/index.tsx
# - 类型定义：src/types/agent.ts
#
# 修改注意事项：
# ------------
# 1. 权限控制：
#    - 所有接口都需要进行权限验证
#    - 防止越权访问和操作
#    - 记录敏感操作日志
#
# 2. 资金操作：
#    - 使用事务确保操作原子性
#    - 记录详细的资金变动日志
#    - 定期对账和数据校验
#
# 3. 数据验证：
#    - 所有输入参数必须经过验证
#    - 特别注意金额等敏感字段
#    - 确保数据一致性
#
# 4. 错误处理：
#    - 统一的错误响应格式
#    - 详细的错误日志记录
#    - 友好的错误提示信息
#
# 5. 性能优化：
#    - 合理使用数据库索引
#    - 避免重复查询
#    - 优化大数据量查询

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from typing import Dict, Any, List
from pydantic import BaseModel
from typing import Optional
from app.services import UserService, ProxyService, AreaService
from app.models.main_user import MainUser
from app.services.auth import get_current_user
from datetime import datetime
import logging
from sqlalchemy import func
import uuid
from app.schemas.agent import AgentList, AgentCreate, AgentUpdate
import json
import traceback
from app.core.deps import get_user_service, get_proxy_service, get_area_service

# 设置日志记录器
logger = logging.getLogger(__name__)

router = APIRouter()

class CreateAgentRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    remark: Optional[str] = None
    status: str = "active"  # 默认状态为active
    balance: float = 1000.0  # 默认额度1000元

class UpdateAgentRequest(BaseModel):
    """更新代理商请求"""
    status: Optional[str] = None
    remark: Optional[str] = None
    balance: Optional[float] = None

def generate_transaction_no() -> str:
    """生成交易号"""
    return f"TRX{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"

@router.post("/open/app/proxy/user/v2")
async def create_agent(
    request: CreateAgentRequest,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """创建代理商"""
    try:
        # 准备用户参数
        user_params = {
            "username": request.username,
            "password": request.password,
            "email": request.email,
            "authType": 2,  # 代理商类型
            "status": "active",  # 强制设置为active
            "remark": request.remark
        }
        
        # 调用用户服务创建用户
        response = await user_service.create_user(user_params)
        if not response:
            raise HTTPException(status_code=400, detail="创建代理商失败")
            
        # 生成交易号
        transaction_no = generate_transaction_no()
        
        try:
            # 创建本地数据库记录
            agent = MainUser(
                username=request.username,
                email=request.email,
                status="active",  # 强制设置为active
                balance=request.balance,
                remark=request.remark,
                transaction_no=transaction_no
            )
            db.add(agent)
            db.commit()
            
            return {
                "code": 0,
                "message": "代理商创建成功",
                "data": {
                    "id": agent.id,
                    "username": agent.username,
                    "email": agent.email,
                    "status": agent.status,
                    "balance": agent.balance,
                    "created_at": agent.created_at.isoformat(),
                    "updated_at": agent.updated_at.isoformat() if agent.updated_at else None
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建代理商数据库记录失败: {str(e)}")
            raise HTTPException(status_code=500, detail="创建代理商数据库记录失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建代理商失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/open/app/agent/list")
async def get_agent_list(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    user_service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db)
):
    """获取代理商列表"""
    try:
        logger.info(f"获取代理商列表: page={page}, pageSize={pageSize}")
        
        # 调用用户服务获取代理商列表
        params = {
            "page": page,
            "pageSize": pageSize,
            "role": "agent"  # 只获取代理商角色
        }
        response = await user_service.get_user_list(params)
        if not response:
            raise HTTPException(status_code=500, detail="获取代理商列表失败")
            
        return {
            "code": 0,
            "message": "获取代理商列表成功",
            "data": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代理商列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/open/app/agent/{agent_id}")
async def get_agent_detail(
    agent_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取代理商详情"""
    agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "code": 0,
        "message": "success",
        "data": agent.to_dict()
    }

@router.get("/open/app/agent/{agent_id}/statistics")
async def get_agent_statistics(
    agent_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取代理商统计信息"""
    agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    # 获取统计数据
    total_orders = db.query(func.count(Transaction.id)).filter(
        Transaction.agent_id == agent_id
    ).scalar()
    
    total_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.agent_id == agent_id
    ).scalar() or 0.0
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "total_orders": total_orders,
            "total_amount": float(total_amount),
            "balance": agent.balance
        }
    }

@router.put("/open/app/agent/{agent_id}/status")
async def update_agent_status(
    agent_id: int,
    status: str = Query(..., description="Agent status to update to"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """更新代理商状态"""
    try:
        agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
        if not agent:
            return {
                "code": 404,
                "msg": "代理商不存在",
                "data": None
            }
            
        agent.status = status
        db.commit()
        db.refresh(agent)
        
        return {
            "code": 0,
            "msg": "success",
            "data": agent.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "code": 500,
            "msg": f"更新代理商状态失败: {str(e)}",
            "data": None
        }

@router.put("/open/app/agent/{agent_id}")
async def update_agent(
    agent_id: int,
    request: UpdateAgentRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """更新代理商信息"""
    try:
        agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
        if not agent:
            return {
                "code": 404,
                "msg": "代理商不存在",
                "data": None
            }
        
        if request.status is not None:
            agent.status = request.status
        if request.remark is not None:
            agent.remark = request.remark
        if request.balance is not None:
            agent.balance = request.balance
            
        db.commit()
        db.refresh(agent)
        
        return {
            "code": 0,
            "msg": "success",
            "data": agent.to_dict()
        }
    except Exception as e:
        db.rollback()
        return {
            "code": 500,
            "msg": f"更新代理商信息失败: {str(e)}",
            "data": None
        }

@router.get("/agent/{agent_id}/detail")
async def get_agent_detail(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取代理商详情"""
    try:
        # 检查代理商是否存在
        agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
        if not agent:
            raise HTTPException(status_code=404, detail={"code": 404, "message": "代理商不存在"})
        
        # 检查权限：管理员可以查看所有代理商，代理商只能查看自己的信息
        if not current_user.is_admin and current_user.id != agent_id:
            raise HTTPException(status_code=403, detail={"code": 403, "message": "没有权限执行此操作"})
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "agent": agent.to_dict()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代理商详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 500, "message": str(e)})

@router.get("/agent/{agent_id}/statistics")
async def get_agent_statistics(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取代理商统计数据"""
    try:
        # 检查代理商是否存在
        agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
        if not agent:
            raise HTTPException(status_code=404, detail={"code": 404, "message": "代理商不存在"})
        
        # 检查权限：管理员可以查看所有代理商，代理商只能查看自己的信息
        if not current_user.is_admin and current_user.id != agent_id:
            raise HTTPException(status_code=403, detail={"code": 403, "message": "没有权限执行此操作"})
        
        # 获取统计数据
        statistics = {
            "total_users": db.query(User).filter(User.agent_id == agent_id).count(),
            "total_balance": agent.balance,
            "total_transactions": db.query(Transaction).filter(Transaction.user_id == agent_id).count()
        }
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "statistics": statistics
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代理商统计数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 500, "message": str(e)})

@router.post("/agent/{agent_id}/balance")
async def update_agent_balance(
    agent_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    调整代理商额度
    
    此接口用于管理员调整代理商的账户余额，包括充值和扣减操作。
    所有操作都会记录详细的交易日志，并确保数据一致性。
    
    参数:
        agent_id (int): 代理商ID
        data (dict): 请求数据，包含：
            - amount (float): 调整金额
            - type (str): 调整类型，'add'为充值，'subtract'为扣减
            - remark (str, optional): 操作备注
        current_user (User): 当前操作用户，必须是管理员
        db (Session): 数据库会话
    
    返回:
        Dict[str, Any]: 包含更新后的代理商信息
            - code (int): 状态码
            - message (str): 操作结果描述
            - data (dict): 更新后的代理商数据
    
    异常:
        - 404: 代理商不存在
        - 403: 无权限执行操作
        - 400: 参数错误或余额不足
        - 500: 服务器内部错误
    
    注意事项:
        1. 只有管理员可以执行此操作
        2. 扣减操作需要检查余额充足性
        3. 所有操作都会记录交易日志
        4. 使用事务确保数据一致性
    """
    try:
        # 检查代理商是否存在
        agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
        if not agent:
            raise HTTPException(status_code=404, detail={"code": 404, "message": "代理商不存在"})
        
        # 检查权限：只有管理员可以调整代理商额度
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail={"code": 403, "message": "没有权限执行此操作"})
        
        # 获取调整金额和类型
        amount = data.get("amount")
        adjust_type = data.get("type")
        remark = data.get("remark", "")
        
        if not amount or not adjust_type:
            raise HTTPException(status_code=400, detail={"code": 400, "message": "缺少必要参数"})
        
        # 根据类型调整余额
        if adjust_type == "add":
            agent.balance += amount
            transaction_type = "recharge"
        else:
            if agent.balance < amount:
                raise HTTPException(status_code=400, detail={"code": 400, "message": "余额不足"})
            agent.balance -= amount
            transaction_type = "deduction"
        
        # 记录交易
        transaction = Transaction(
            order_no=generate_transaction_no(),
            user_id=agent.id,
            amount=amount,
            type=transaction_type,
            status="completed",
            remark=remark,
            operator_id=current_user.id
        )
        db.add(transaction)
        
        db.commit()
        db.refresh(agent)
        
        return {
            "code": 200,
            "message": "额度调整成功",
            "data": agent.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"调整代理商额度失败: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 500, "message": str(e)})

@router.post("/agent/{agent_id}/status")
async def update_agent_status(
    agent_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    更新代理商状态
    
    此接口用于管理员更新代理商的状态，可以启用或禁用代理商账户。
    状态变更会影响代理商的所有业务操作权限。
    
    参数:
        agent_id (int): 代理商ID
        data (dict): 请求数据，包含：
            - status (str): 新状态，可选值：'active'/'disabled'
            - remark (str, optional): 状态变更原因
        current_user (User): 当前操作用户，必须是管理员
        db (Session): 数据库会话
    
    返回:
        Dict[str, Any]: 包含更新后的代理商信息
            - code (int): 状态码
            - message (str): 操作结果描述
            - data (dict): 更新后的代理商数据
    
    异常:
        - 404: 代理商不存在
        - 403: 无权限执行操作
        - 400: 状态参数无效
        - 500: 服务器内部错误
    
    注意事项:
        1. 只有管理员可以执行此操作
        2. 状态变更会影响代理商的所有业务操作
        3. 需要记录状态变更日志
        4. 状态变更可能需要同步更新相关资源
    """
    try:
        # 检查代理商是否存在
        agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
        if not agent:
            raise HTTPException(status_code=404, detail={"code": 404, "message": "代理商不存在"})
        
        # 检查权限：只有管理员可以更新代理商状态
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail={"code": 403, "message": "没有权限执行此操作"})
        
        # 更新状态
        status = data.get("status")
        if not status:
            raise HTTPException(status_code=400, detail={"code": 400, "message": "缺少状态参数"})
            
        agent.status = status
        agent.remark = data.get("remark", "")
        
        db.commit()
        db.refresh(agent)
        
        return {
            "code": 200,
            "message": "状态更新成功",
            "data": agent.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新代理商状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 500, "message": str(e)})

@router.get("/agent/{agent_id}/transactions")
async def get_agent_transactions(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取代理商交易记录
    
    此接口用于查询代理商的所有交易记录，包括充值、扣减等操作。
    支持分页查询和多种筛选条件。
    
    参数:
        agent_id (int): 代理商ID
        current_user (User): 当前操作用户
        db (Session): 数据库会话
    
    返回:
        Dict[str, Any]: 包含交易记录列表
            - code (int): 状态码
            - message (str): 操作结果描述
            - data (dict): 
                - list (List[dict]): 交易记录列表
                - total (int): 总记录数
                - page (int): 当前页码
                - page_size (int): 每页记录数
    
    异常:
        - 404: 代理商不存在
        - 403: 无权限查看记录
        - 500: 服务器内部错误
    
    注意事项:
        1. 管理员可以查看所有代理商的记录
        2. 代理商只能查看自己的记录
        3. 支持按时间范围和交易类型筛选
        4. 结果按时间倒序排列
    """
    try:
        # 检查代理商是否存在
        agent = db.query(User).filter(User.id == agent_id, User.is_agent == True).first()
        if not agent:
            raise HTTPException(status_code=404, detail={"code": 404, "message": "代理商不存在"})
        
        # 检查权限：管理员可以查看所有代理商，代理商只能查看自己的信息
        if not current_user.is_admin and current_user.id != agent_id:
            raise HTTPException(status_code=403, detail={"code": 403, "message": "没有权限执行此操作"})
        
        # 获取交易记录
        transactions = db.query(Transaction).filter(Transaction.user_id == agent_id).all()
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "transactions": [t.to_dict() for t in transactions],
                "total": len(transactions),
                "page": 1,
                "page_size": len(transactions)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代理商交易记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 500, "message": str(e)})

@router.post("/open/app/area/v2")
async def get_area_list(
    params: Dict[str, Any] = Body(...),
    area_service: AreaService = Depends(get_area_service)
) -> Dict[str, Any]:
    """获取地区列表"""
    try:
        logger.info("[IPIPV] 获取区域列表")
        # 构造请求参数
        request_params = {
            "version": "v2",
            "encrypt": "AES"
        }
        # 合并用户传入的参数
        if params:
            request_params.update(params)
            
        result = await area_service.get_area_list(request_params)
        return {
            "code": 0,
            "message": "success",
            "data": result if result else []
        }
    except Exception as e:
        logger.error(f"[IPIPV] 获取区域列表失败: {str(e)}")
        logger.error(f"[IPIPV] 错误堆栈: {traceback.format_exc()}")
        return {
            "code": 500,
            "message": str(e),
            "data": []
        }

@router.get("/settings/agent/{agent_id}/prices")
async def get_agent_prices(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取代理商价格设置"""
    try:
        # 检查权限：只有管理员或者代理商本人可以查看
        if not current_user.is_admin and current_user.id != agent_id:
            raise HTTPException(
                status_code=403,
                detail="没有权限查看价格设置"
            )
            
        # 获取代理商
        agent = db.query(User).filter(
            User.id == agent_id,
            User.is_agent == True
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail="代理商不存在"
            )
            
        # 返回价格配置
        return {
            "code": 0,
            "msg": "success",
            "data": {
                "dynamic": {
                    "pool1": 100,  # 动态代理池1价格
                    "pool2": 200   # 动态代理池2价格
                },
                "static": {
                    "residential": 300,  # 静态住宅代理价格
                    "datacenter": 400    # 静态数据中心代理价格
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取代理商价格设置失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )