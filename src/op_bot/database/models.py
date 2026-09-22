"""SQLAlchemy 2.0 ORM models; constraints enforce one-time rewards/referrals."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
class Base(DeclarativeBase): pass
class User(Base):
 __tablename__='users'; id: Mapped[int]=mapped_column(BigInteger,primary_key=True); telegram_id: Mapped[int]=mapped_column(BigInteger,unique=True); username: Mapped[str|None]=mapped_column(String(255)); first_name: Mapped[str|None]=mapped_column(String(255)); referrer_id: Mapped[int|None]=mapped_column(ForeignKey('users.id')); stars_balance: Mapped[int]=mapped_column(Integer,default=0); is_blocked: Mapped[bool]=mapped_column(Boolean,default=False); sponsors_completed: Mapped[bool]=mapped_column(Boolean,default=False); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
class Referral(Base):
 __tablename__='referrals'; __table_args__=(UniqueConstraint('referred_id'),); id: Mapped[int]=mapped_column(BigInteger,primary_key=True); referrer_id: Mapped[int]=mapped_column(ForeignKey('users.id')); referred_id: Mapped[int]=mapped_column(ForeignKey('users.id')); status: Mapped[str]=mapped_column(String(16),default='pending'); reward: Mapped[int]=mapped_column(Integer,default=0)
class Task(Base):
 __tablename__='tasks'; __table_args__=(UniqueConstraint('user_id','resource_id'),); id: Mapped[int]=mapped_column(BigInteger,primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); resource_id: Mapped[str]=mapped_column(String); url: Mapped[str]=mapped_column(Text); status: Mapped[str]=mapped_column(String(32),default='received'); reward: Mapped[int]=mapped_column(Integer,default=0); rewarded: Mapped[bool]=mapped_column(Boolean,default=False); completed_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
class StarTransaction(Base):
 __tablename__='star_transactions'; id: Mapped[int]=mapped_column(BigInteger,primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); amount: Mapped[int]=mapped_column(Integer); type: Mapped[str]=mapped_column(String(16)); source_id: Mapped[str|None]=mapped_column(String); description: Mapped[str]=mapped_column(Text)
class BlockedResourceModel(Base):
 __tablename__='blocked_resources'
 id: Mapped[int]=mapped_column(BigInteger,primary_key=True)
 resource_id: Mapped[str]=mapped_column(String)
 url: Mapped[str]=mapped_column(Text)
 reason: Mapped[str|None]=mapped_column(Text)
 blocked_by: Mapped[int]=mapped_column(BigInteger)
 is_active: Mapped[bool]=mapped_column(Boolean,default=True)
