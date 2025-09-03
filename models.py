from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(String, primary_key=True)
    customer_id = Column(String, nullable=False)
    status = Column(String, default='pending')
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("OrderItem", back_populates="order")
    payments = relationship("Payment", back_populates="order")
    
class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey('orders.id'), nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey('orders.id'), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default='pending')
    payment_method = Column(String, nullable=False)
    transaction_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="payments")

class Inventory(Base):
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reservations = relationship("InventoryReservation", back_populates="inventory")

class InventoryReservation(Base):
    __tablename__ = 'inventory_reservations'
    
    id = Column(String, primary_key=True)
    product_id = Column(String, ForeignKey('inventory.product_id'), nullable=False)
    order_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, default='active')  # active, released, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    inventory = relationship("Inventory", back_populates="reservations")

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(String, primary_key=True)
    recipient = Column(String, nullable=False)
    type = Column(String, nullable=False)  # email, sms, push
    template = Column(String, nullable=False)
    subject = Column(String)
    message = Column(Text, nullable=False)
    status = Column(String, default='pending')  # pending, sent, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    error_message = Column(Text)

class OrderFlow(Base):
    __tablename__ = 'order_flows'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, nullable=False)
    step = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

# Database connection and session management
class DatabaseManager:
    def __init__(self, database_url=None):
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///ecommerce.db')
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def init_sample_data(self):
        """Initialize database with sample data"""
        session = self.get_session()
        try:
            # Check if data already exists
            if session.query(Inventory).count() > 0:
                return
            
            # Add sample inventory
            sample_products = [
                {'product_id': 'LAPTOP001', 'name': 'Gaming Laptop', 'quantity': 50, 'price': 1299.99},
                {'product_id': 'PHONE001', 'name': 'Smartphone', 'quantity': 100, 'price': 699.99},
                {'product_id': 'TABLET001', 'name': 'Tablet', 'quantity': 75, 'price': 399.99},
                {'product_id': 'HEADPHONES001', 'name': 'Wireless Headphones', 'quantity': 200, 'price': 199.99},
                {'product_id': 'WATCH001', 'name': 'Smart Watch', 'quantity': 80, 'price': 299.99}
            ]
            
            for product_data in sample_products:
                inventory = Inventory(**product_data)
                session.add(inventory)
            
            session.commit()
            print("Sample data initialized successfully")
        except Exception as e:
            session.rollback()
            print(f"Error initializing sample data: {e}")
        finally:
            session.close()

# Global database manager instance
db_manager = DatabaseManager()