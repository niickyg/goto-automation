"""
Database models and connection management.

SQLAlchemy models for calls, summaries, action items, and KPIs.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool
import enum
import logging

from config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()


# Enums
class SentimentType(str, enum.Enum):
    """Sentiment classification."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class ActionItemStatus(str, enum.Enum):
    """Action item status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CallDirection(str, enum.Enum):
    """Call direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


# Models
class Call(Base):
    """Call record from GoTo Connect."""

    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goto_call_id = Column(String(255), unique=True, nullable=False, index=True)
    direction = Column(SQLEnum(CallDirection), nullable=False)
    caller_number = Column(String(50), nullable=True)
    caller_name = Column(String(255), nullable=True)
    called_number = Column(String(50), nullable=True)
    called_name = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    recording_url = Column(Text, nullable=True)
    recording_downloaded = Column(Boolean, default=False)
    recording_file_path = Column(Text, nullable=True)
    webhook_received_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    summary = relationship("CallSummary", back_populates="call", uselist=False)
    action_items = relationship("ActionItem", back_populates="call")

    def __repr__(self):
        return f"<Call(id={self.id}, goto_call_id={self.goto_call_id}, start_time={self.start_time})>"


class CallSummary(Base):
    """AI-generated call summary."""

    __tablename__ = "call_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(Integer, ForeignKey("calls.id"), unique=True, nullable=False, index=True)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment = Column(SQLEnum(SentimentType), nullable=True)
    urgency_score = Column(Integer, nullable=True)  # 1-5
    key_topics = Column(Text, nullable=True)  # JSON array stored as text
    transcription_started_at = Column(DateTime, nullable=True)
    transcription_completed_at = Column(DateTime, nullable=True)
    analysis_started_at = Column(DateTime, nullable=True)
    analysis_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    call = relationship("Call", back_populates="summary")

    def __repr__(self):
        return f"<CallSummary(id={self.id}, call_id={self.call_id}, sentiment={self.sentiment})>"


class ActionItem(Base):
    """Action items extracted from calls."""

    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(Integer, ForeignKey("calls.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    assigned_to = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(
        SQLEnum(ActionItemStatus),
        default=ActionItemStatus.PENDING,
        nullable=False,
        index=True
    )
    priority = Column(Integer, nullable=True)  # 1-5
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    call = relationship("Call", back_populates="action_items")

    def __repr__(self):
        return f"<ActionItem(id={self.id}, call_id={self.call_id}, status={self.status})>"


class KPI(Base):
    """Daily/weekly/monthly KPI metrics."""

    __tablename__ = "kpis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    total_calls = Column(Integer, default=0)
    total_duration_seconds = Column(Integer, default=0)
    avg_duration_seconds = Column(Float, nullable=True)
    inbound_calls = Column(Integer, default=0)
    outbound_calls = Column(Integer, default=0)
    calls_with_recordings = Column(Integer, default=0)
    calls_transcribed = Column(Integer, default=0)
    positive_sentiment_count = Column(Integer, default=0)
    neutral_sentiment_count = Column(Integer, default=0)
    negative_sentiment_count = Column(Integer, default=0)
    avg_urgency_score = Column(Float, nullable=True)
    total_action_items = Column(Integer, default=0)
    completed_action_items = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_kpis_period', 'period_type', 'period_start'),
    )

    def __repr__(self):
        return f"<KPI(id={self.id}, period_type={self.period_type}, period_start={self.period_start})>"


# Database connection
class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self):
        """Initialize database manager."""
        self.engine = None
        self.SessionLocal = None
        self._initialized = False

    def initialize(self):
        """Initialize database engine and session factory."""
        if self._initialized:
            return

        settings = get_settings()

        self.engine = create_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.log_level == "DEBUG",
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self._initialized = True
        logger.info("Database initialized successfully")

    def create_tables(self):
        """Create all tables in the database."""
        if not self._initialized:
            self.initialize()
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy session instance.
        """
        if not self._initialized:
            self.initialize()
        return self.SessionLocal()

    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Session:
    """
    Dependency for getting database sessions.

    Yields:
        Database session that is automatically closed after use.
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


# CRUD Operations
class CallRepository:
    """Repository for Call operations."""

    @staticmethod
    def create(session: Session, **kwargs) -> Call:
        """Create a new call record."""
        call = Call(**kwargs)
        session.add(call)
        session.commit()
        session.refresh(call)
        logger.info(f"Created call: {call.goto_call_id}")
        return call

    @staticmethod
    def get_by_goto_id(session: Session, goto_call_id: str) -> Optional[Call]:
        """Get call by GoTo call ID."""
        return session.query(Call).filter(Call.goto_call_id == goto_call_id).first()

    @staticmethod
    def get_by_id(session: Session, call_id: int) -> Optional[Call]:
        """Get call by database ID."""
        return session.query(Call).filter(Call.id == call_id).first()

    @staticmethod
    def list_calls(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Call]:
        """List calls with pagination and optional date filtering."""
        query = session.query(Call).order_by(Call.start_time.desc())

        if start_date:
            query = query.filter(Call.start_time >= start_date)
        if end_date:
            query = query.filter(Call.start_time <= end_date)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(session: Session, call: Call, **kwargs):
        """Update call record."""
        for key, value in kwargs.items():
            setattr(call, key, value)
        session.commit()
        session.refresh(call)
        return call


class SummaryRepository:
    """Repository for CallSummary operations."""

    @staticmethod
    def create(session: Session, **kwargs) -> CallSummary:
        """Create a new call summary."""
        summary = CallSummary(**kwargs)
        session.add(summary)
        session.commit()
        session.refresh(summary)
        logger.info(f"Created summary for call_id: {summary.call_id}")
        return summary

    @staticmethod
    def get_by_call_id(session: Session, call_id: int) -> Optional[CallSummary]:
        """Get summary by call ID."""
        return session.query(CallSummary).filter(CallSummary.call_id == call_id).first()

    @staticmethod
    def update(session: Session, summary: CallSummary, **kwargs):
        """Update summary record."""
        for key, value in kwargs.items():
            setattr(summary, key, value)
        session.commit()
        session.refresh(summary)
        return summary


class ActionItemRepository:
    """Repository for ActionItem operations."""

    @staticmethod
    def create(session: Session, **kwargs) -> ActionItem:
        """Create a new action item."""
        action_item = ActionItem(**kwargs)
        session.add(action_item)
        session.commit()
        session.refresh(action_item)
        logger.info(f"Created action item for call_id: {action_item.call_id}")
        return action_item

    @staticmethod
    def get_by_id(session: Session, action_id: int) -> Optional[ActionItem]:
        """Get action item by ID."""
        return session.query(ActionItem).filter(ActionItem.id == action_id).first()

    @staticmethod
    def list_by_status(
        session: Session,
        status: ActionItemStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[ActionItem]:
        """List action items by status."""
        return (
            session.query(ActionItem)
            .filter(ActionItem.status == status)
            .order_by(ActionItem.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update(session: Session, action_item: ActionItem, **kwargs):
        """Update action item."""
        for key, value in kwargs.items():
            setattr(action_item, key, value)

        # Set completed_at if status changed to completed
        if kwargs.get("status") == ActionItemStatus.COMPLETED and not action_item.completed_at:
            action_item.completed_at = datetime.utcnow()

        session.commit()
        session.refresh(action_item)
        return action_item

    @staticmethod
    def delete(session: Session, action_item: ActionItem) -> bool:
        """Delete an action item."""
        try:
            session.delete(action_item)
            session.commit()
            logger.info(f"Deleted action item {action_item.id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete action item {action_item.id}: {e}")
            return False


class KPIRepository:
    """Repository for KPI operations."""

    @staticmethod
    def create(session: Session, **kwargs) -> KPI:
        """Create a new KPI record."""
        kpi = KPI(**kwargs)
        session.add(kpi)
        session.commit()
        session.refresh(kpi)
        logger.info(f"Created KPI: {kpi.period_type} for {kpi.period_start}")
        return kpi

    @staticmethod
    def get_or_create(
        session: Session,
        period_type: str,
        period_start: datetime,
        period_end: datetime
    ) -> KPI:
        """Get existing KPI or create new one."""
        kpi = (
            session.query(KPI)
            .filter(
                KPI.period_type == period_type,
                KPI.period_start == period_start
            )
            .first()
        )

        if not kpi:
            kpi = KPIRepository.create(
                session,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end
            )

        return kpi


if __name__ == "__main__":
    # Test database connection
    from config import configure_logging

    configure_logging()
    db_manager.initialize()
    db_manager.create_tables()
    print("Database initialized and tables created successfully!")
