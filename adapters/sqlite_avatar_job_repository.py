"""SQLite-backed avatar job repository adapter."""

from __future__ import annotations

from sqlalchemy import Column, DateTime, String, create_engine, select
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ports.outbound.avatar_job_repository import AvatarJobRepositoryPort
from services.avatar_generation.models import AvatarJob, AvatarJobStatus


Base = declarative_base()


class AvatarJobRecord(Base):
    """SQLite persistence model for avatar jobs."""

    __tablename__ = "avatar_jobs"

    job_id = Column(String(64), primary_key=True)
    script = Column(String(300), nullable=False)
    voice = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    image_path = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    generated_video_path = Column(String(512), nullable=True)
    provider_error_message = Column(String(512), nullable=True)


def _to_domain(record: AvatarJobRecord) -> AvatarJob:
    return AvatarJob(
        job_id=record.job_id,
        script=record.script,
        voice=record.voice,
        status=AvatarJobStatus(record.status),
        image_path=record.image_path,
        created_at=record.created_at,
        updated_at=record.updated_at,
        generated_video_path=record.generated_video_path,
        provider_error_message=record.provider_error_message,
    )


class SQLiteAvatarJobRepositoryAdapter(AvatarJobRepositoryPort):
    """Persists avatar jobs in SQLite using SQLAlchemy."""

    def __init__(self, database_url: str) -> None:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self._engine = create_engine(database_url, future=True, connect_args=connect_args)
        self._session_factory = sessionmaker(self._engine, expire_on_commit=False, class_=Session)
        Base.metadata.create_all(self._engine)

    def create(self, job: AvatarJob) -> AvatarJob:
        with self._session_factory() as session:
            record = AvatarJobRecord(
                job_id=job.job_id,
                script=job.script,
                voice=job.voice,
                status=job.status.value,
                image_path=job.image_path,
                created_at=job.created_at,
                updated_at=job.updated_at,
                generated_video_path=job.generated_video_path,
                provider_error_message=job.provider_error_message,
            )
            session.add(record)
            session.commit()
            return _to_domain(record)

    def get_by_id(self, job_id: str) -> AvatarJob | None:
        with self._session_factory() as session:
            record = session.get(AvatarJobRecord, job_id)
            if record is None:
                return None
            return _to_domain(record)

    def update(self, job: AvatarJob) -> AvatarJob:
        with self._session_factory() as session:
            record = session.get(AvatarJobRecord, job.job_id)
            if record is None:
                raise ValueError(f"Avatar job {job.job_id} does not exist.")
            record.script = job.script
            record.voice = job.voice
            record.status = job.status.value
            record.image_path = job.image_path
            record.created_at = job.created_at
            record.updated_at = job.updated_at
            record.generated_video_path = job.generated_video_path
            record.provider_error_message = job.provider_error_message
            session.commit()
            return _to_domain(record)

    def count(self) -> int:
        """Return the number of persisted jobs for tests and local diagnostics."""

        with self._session_factory() as session:
            return len(session.scalars(select(AvatarJobRecord)).all())
