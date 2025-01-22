from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_test_data():
    """初始化测试数据"""
    from .models.dashboard import ProxyInfo, ResourceUsage
    
    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(ProxyInfo).first() is None:
            # 创建代理信息
            proxy_info = ProxyInfo(
                balance=1000.0,
                total_recharge=5000.0,
                total_consumption=4000.0,
                month_recharge=1000.0,
                month_consumption=800.0,
                last_month_consumption=1200.0
            )
            db.add(proxy_info)
            
            # 创建动态资源使用信息
            dynamic_resources = [
                ResourceUsage(
                    resource_type="dynamic",
                    title="动态住宅IP",
                    total=10000,
                    used=5000,
                    today=200,
                    last_month=4500,
                    percentage=50.0
                ),
                ResourceUsage(
                    resource_type="dynamic",
                    title="动态数据中心",
                    total=5000,
                    used=2000,
                    today=100,
                    last_month=2200,
                    percentage=40.0
                )
            ]
            db.add_all(dynamic_resources)
            
            # 创建静态资源使用信息
            static_resources = [
                ResourceUsage(
                    resource_type="static",
                    title="静态住宅IP",
                    total=1000,
                    used=400,
                    today=50,
                    last_month=600,
                    available=600,
                    percentage=40.0
                ),
                ResourceUsage(
                    resource_type="static",
                    title="静态数据中心",
                    total=500,
                    used=200,
                    today=30,
                    last_month=300,
                    available=300,
                    percentage=40.0
                )
            ]
            db.add_all(static_resources)
            
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
