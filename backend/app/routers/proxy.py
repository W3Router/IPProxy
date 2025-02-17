"""
代理服务路由模块
==============

此模块处理所有与代理服务相关的路由请求，包括：
- 动态代理管理
- 静态代理管理
- 代理池管理
- 价格计算
- 流量统计

重要提示：
---------
1. 所有API路由都需要遵循统一的响应格式
2. 错误处理需要保持一致性
3. 日志记录需要包含关键信息

依赖关系：
---------
- 数据模型：
  - ProxyInfo (app/models/dashboard.py)
  - FlowUsage (app/models/transaction.py)
- 服务层：
  - ProxyService (app/services/proxy.py)
- 前端对应：
  - 服务层：src/services/proxyService.ts
  - 组件：src/pages/proxy/index.tsx

修改注意事项：
------------
1. API路由：
   - 保持与API文档的一致性
   - 确保与前端请求路径匹配
   - 维护版本兼容性

2. 参数验证：
   - 所有输入参数需要进行验证
   - 特别注意敏感参数的处理
   - 保持与前端类型定义的一致性

3. 错误处理：
   - 统一的错误响应格式
   - 详细的错误日志记录
   - 合适的错误码使用

4. 数据处理：
   - 注意数据类型转换
   - 处理空值和默认值
   - 保持数据一致性

5. 性能考虑：
   - 避免重复的API调用
   - 合理使用数据库会话
   - 考虑并发请求处理
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.dashboard import ProxyInfo
from app.models.transaction import FlowUsage
from app.core.deps import get_proxy_service
from app.services import ProxyService
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

def log_request_info(func_name: str, **kwargs):
    """记录请求信息的辅助函数"""
    logger.info(f"[{func_name}] Request started at {datetime.now()}")
    logger.info(f"[{func_name}] Parameters: {json.dumps(kwargs, ensure_ascii=False)}")

def log_response_info(func_name: str, response: Any):
    """记录响应信息的辅助函数"""
    logger.info(f"[{func_name}] Response: {json.dumps(response, ensure_ascii=False)}")
    logger.info(f"[{func_name}] Request completed at {datetime.now()}")

@router.get("/open/app/proxy/dynamic/list/v2")
async def get_dynamic_proxy_list(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    ip: Optional[str] = None,
    status: Optional[str] = None,
    protocol: Optional[str] = None,
    proxy_service: ProxyService = Depends(get_proxy_service),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取动态代理列表"""
    func_name = "get_dynamic_proxy_list"
    try:
        log_request_info(func_name, page=page, pageSize=pageSize, ip=ip, status=status, protocol=protocol)
        
        params = {
            "page": page,
            "pageSize": pageSize,
            "proxyType": 104,  # 动态代理类型
        }
        if ip:
            params["ip"] = ip
        if status:
            params["status"] = status
        if protocol:
            params["protocol"] = protocol
            
        logger.info(f"[{func_name}] Calling ProxyService with params: {json.dumps(params, ensure_ascii=False)}")
        response = await proxy_service.get_dynamic_proxy_list(params)
        logger.info(f"[{func_name}] Service response: {json.dumps(response, ensure_ascii=False)}")
        
        result = {
            "code": 0,
            "msg": "success",
            "data": response
        }
        log_response_info(func_name, result)
        return result
    except Exception as e:
        logger.error(f"[{func_name}] Error: {str(e)}", exc_info=True)
        logger.error(f"[{func_name}] Stack trace:", stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/open/app/proxy/pools/v2")
async def get_proxy_pools(
    proxy_service: ProxyService = Depends(get_proxy_service),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取代理池列表"""
    func_name = "get_proxy_pools"
    try:
        log_request_info(func_name)
        
        logger.info(f"[{func_name}] Calling ProxyService for proxy pools")
        response = await proxy_service.get_proxy_pools(104)  # 动态代理类型
        logger.info(f"[{func_name}] Service response: {json.dumps(response, ensure_ascii=False)}")
        
        result = {
            "code": 0,
            "msg": "success",
            "data": response
        }
        log_response_info(func_name, result)
        return result
    except Exception as e:
        logger.error(f"[{func_name}] Error: {str(e)}", exc_info=True)
        logger.error(f"[{func_name}] Stack trace:", stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open/app/proxy/price/calculate/v2")
async def calculate_proxy_price(
    poolId: str,
    trafficAmount: int,
    proxy_service: ProxyService = Depends(get_proxy_service),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """计算代理价格"""
    func_name = "calculate_proxy_price"
    try:
        log_request_info(func_name, poolId=poolId, trafficAmount=trafficAmount)
        
        params = {
            "poolId": poolId,
            "trafficAmount": trafficAmount
        }
        logger.info(f"[{func_name}] Calling ProxyService with params: {json.dumps(params, ensure_ascii=False)}")
        response = await proxy_service.calculate_price(params)
        logger.info(f"[{func_name}] Service response: {json.dumps(response, ensure_ascii=False)}")
        
        result = {
            "code": 0,
            "msg": "success",
            "data": {
                "price": float(response.get("price", 0))
            }
        }
        log_response_info(func_name, result)
        return result
    except Exception as e:
        logger.error(f"[{func_name}] Error: {str(e)}", exc_info=True)
        logger.error(f"[{func_name}] Stack trace:", stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open/app/proxy/open/v2")
async def open_dynamic_proxy(
    poolId: str,
    trafficAmount: int,
    username: Optional[str] = None,
    password: Optional[str] = None,
    remark: Optional[str] = None,
    proxy_service: ProxyService = Depends(get_proxy_service),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """开通动态代理"""
    try:
        params = {
            "poolId": poolId,
            "trafficAmount": trafficAmount,
            "proxyType": 104  # 动态代理类型
        }
        if username:
            params["username"] = username
        if password:
            params["password"] = password
        if remark:
            params["remark"] = remark
            
        response = await proxy_service.open_proxy(params)
        return {
            "code": 0,
            "msg": "success",
            "data": response
        }
    except Exception as e:
        logger.error(f"开通动态代理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open/app/proxy/refresh/v2/{orderNo}")
async def refresh_dynamic_proxy(
    orderNo: str,
    proxy_service: ProxyService = Depends(get_proxy_service),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """刷新动态代理"""
    try:
        response = await proxy_service.refresh_proxy(orderNo)
        return {
            "code": 0,
            "msg": "success",
            "data": response
        }
    except Exception as e:
        logger.error(f"刷新动态代理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/open/app/proxy/info/v2")
async def get_proxy_info(
    proxy_service: ProxyService = Depends(get_proxy_service),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取代理信息"""
    try:
        proxy_info = await proxy_service.get_proxy_info()
        return {
            "code": 0,
            "msg": "success",
            "data": proxy_info
        }
    except Exception as e:
        logger.error(f"获取代理信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/open/app/proxy/flow/use/log/v2")
async def get_flow_usage(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """获取流量使用记录"""
    flow_usage = db.query(FlowUsage).first()
    if not flow_usage:
        # 如果没有数据，创建测试数据
        flow_usage = FlowUsage(
            monthly_usage=150.5,    # 本月已使用 150.5GB
            daily_usage=5.2,        # 今日已使用 5.2GB
            last_month_usage=200.8  # 上月使用 200.8GB
        )
        db.add(flow_usage)
        db.commit()
        db.refresh(flow_usage)
    
    return {
        "code": "200",
        "msg": "success",
        "data": {
            "monthlyUsage": flow_usage.monthly_usage,
            "dailyUsage": flow_usage.daily_usage,
            "lastMonthUsage": flow_usage.last_month_usage
        }
    }

@router.post("/open/app/product/query/v2")
async def query_product(
    request: Dict[str, Any],
    proxy_service: ProxyService = Depends(get_proxy_service),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """查询产品信息"""
    func_name = "query_product"
    try:
        logger.info(f"[{func_name}] 开始处理请求")
        logger.info(f"[{func_name}] 请求参数类型: {type(request)}")
        logger.info(f"[{func_name}] 请求参数内容: {json.dumps(request, ensure_ascii=False)}")
        
        # 处理加密参数
        if "params" in request:
            try:
                encrypted_params = request.get("params")
                logger.info(f"[{func_name}] 收到加密参数: {encrypted_params}")
                decrypted_params = proxy_service._decrypt_response(encrypted_params)
                logger.info(f"[{func_name}] 解密后参数: {decrypted_params}")
                if not isinstance(decrypted_params, dict):
                    logger.error(f"[{func_name}] 解密后参数格式错误: {type(decrypted_params)}")
                    return {
                        "code": 400,
                        "msg": "参数格式错误",
                        "data": []
                    }
                request = decrypted_params
            except Exception as e:
                logger.error(f"[{func_name}] 解密参数失败: {str(e)}")
                return {
                    "code": 400,
                    "msg": "参数解密失败",
                    "data": []
                }

        # 参数名称映射
        param_mapping = {
            "regionCode": "regionCode",
            "countryCode": "countryCode",
            "cityCode": "cityCode",
            "proxyType": "proxyType"
        }
        
        mapped_request = {}
        for frontend_key, backend_key in param_mapping.items():
            if frontend_key in request:
                mapped_request[backend_key] = request[frontend_key]
        
        # 验证必要参数
        required_fields = ["regionCode", "countryCode", "cityCode", "proxyType"]
        missing_fields = [field for field in required_fields if field not in mapped_request]
        if missing_fields:
            error_msg = f"缺少必要参数: {', '.join(missing_fields)}"
            logger.error(f"[{func_name}] {error_msg}")
            return {
                "code": 400,
                "msg": error_msg,
                "data": []
            }
            
        # 处理 proxyType 参数
        try:
            proxy_type = mapped_request["proxyType"]
            if isinstance(proxy_type, str):
                if proxy_type.lower() == "static":
                    proxy_type = 1
                elif proxy_type.lower() == "dynamic":
                    proxy_type = 2
                else:
                    proxy_type = int(proxy_type)
            mapped_request["proxyType"] = [proxy_type]  # 转换为数组格式
        except (ValueError, TypeError) as e:
            logger.error(f"[{func_name}] proxyType 转换失败: {str(e)}")
            return {
                "code": 400,
                "msg": "proxyType 参数格式错误",
                "data": []
            }
            
        # 调用服务
        try:
            response = await proxy_service.query_product(mapped_request)
            logger.info(f"[{func_name}] 服务调用成功")
            logger.info(f"[{func_name}] 响应内容: {json.dumps(response, ensure_ascii=False)}")
            
            # 如果没有找到IP段，返回默认的ALL选项
            if not response or len(response) == 0:
                default_response = [{
                    "ipStart": "ALL",
                    "ipEnd": "ALL",
                    "ipCount": 0,
                    "stock": 999999,
                    "staticType": request.get("staticType", "1"),
                    "countryCode": mapped_request["countryCode"],
                    "cityCode": mapped_request["cityCode"],
                    "regionCode": mapped_request["regionCode"],
                    "price": 0,
                    "status": 1
                }]
                return {
                    "code": 0,
                    "msg": "success",
                    "data": default_response
                }
                
            return {
                "code": 0,
                "msg": "success",
                "data": response
            }
        except Exception as e:
            logger.error(f"[{func_name}] 服务调用失败: {str(e)}")
            logger.error(f"[{func_name}] 错误堆栈:", exc_info=True)
            return {
                "code": 500,
                "msg": f"服务调用失败: {str(e)}",
                "data": []
            }
            
    except Exception as e:
        logger.error(f"[{func_name}] Error: {str(e)}")
        return {
            "code": 500,
            "msg": str(e),
            "data": []
        } 