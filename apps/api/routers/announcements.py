"""Announcements router - Notices, Announcements, and Messages."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..database import get_db
from ..models.communication import Notice, Announcement, Message
from ..models.user import User
from ..core.deps import get_current_user, get_current_admin, get_current_teacher

router = APIRouter(prefix="/announcements", tags=["Announcements"])


# ============= Pydantic Schemas =============

class NoticeBase(BaseModel):
    title: str
    content: str
    priority: str = "normal"
    target_roles: Optional[List[str]] = None
    class_section_ids: Optional[List[int]] = None
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_published: bool = False


class NoticeCreate(NoticeBase):
    pass


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    target_roles: Optional[List[str]] = None
    class_section_ids: Optional[List[int]] = None
    publish_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_published: Optional[bool] = None


class NoticeResponse(NoticeBase):
    id: int
    school_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnouncementBase(BaseModel):
    title: str
    body: str
    target_audience: str = "all"
    publish_at: Optional[datetime] = None


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    target_audience: Optional[str] = None
    publish_at: Optional[datetime] = None


class AnnouncementResponse(AnnouncementBase):
    id: int
    school_id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    subject: Optional[str] = None
    body: str


class MessageCreate(MessageBase):
    recipient_id: int


class MessageResponse(MessageBase):
    id: int
    sender_id: int
    recipient_id: int
    is_read: bool
    sent_at: datetime
    read_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============= Notice Endpoints =============

@router.get("/notices", response_model=List[NoticeResponse])
async def list_notices(
    skip: int = 0,
    limit: int = 50,
    is_published: Optional[bool] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List notices. Admins see all, others see only published notices.
    """
    query = select(Notice)

    if current_user.role == "admin":
        if is_published is not None:
            query = query.where(Notice.is_published == is_published)
    else:
        query = query.where(Notice.is_published == True)

    if priority:
        query = query.where(Notice.priority == priority)

    query = query.order_by(Notice.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/notices", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED)
async def create_notice(
    notice: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new notice. Admin only.
    """
    db_notice = Notice(
        school_id=current_user.school_id,
        author_id=current_user.id,
        title=notice.title,
        content=notice.content,
        priority=notice.priority,
        target_roles=notice.target_roles,
        class_section_ids=notice.class_section_ids,
        publish_at=notice.publish_at,
        expires_at=notice.expires_at,
        is_published=notice.is_published,
    )
    db.add(db_notice)
    await db.commit()
    await db.refresh(db_notice)
    return db_notice


@router.get("/notices/{notice_id}", response_model=NoticeResponse)
async def get_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific notice by ID.
    """
    result = await db.execute(select(Notice).where(Notice.id == notice_id))
    notice = result.scalar_one_or_none()

    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")

    if not notice.is_published and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this notice")

    return notice


@router.put("/notices/{notice_id}", response_model=NoticeResponse)
async def update_notice(
    notice_id: int,
    notice_update: NoticeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update a notice. Admin only.
    """
    result = await db.execute(select(Notice).where(Notice.id == notice_id))
    db_notice = result.scalar_one_or_none()

    if not db_notice:
        raise HTTPException(status_code=404, detail="Notice not found")

    update_data = notice_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_notice, field, value)

    await db.commit()
    await db.refresh(db_notice)
    return db_notice


@router.delete("/notices/{notice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a notice. Admin only.
    """
    result = await db.execute(select(Notice).where(Notice.id == notice_id))
    db_notice = result.scalar_one_or_none()

    if not db_notice:
        raise HTTPException(status_code=404, detail="Notice not found")

    await db.delete(db_notice)
    await db.commit()


# ============= Announcement Endpoints =============

@router.get("/", response_model=List[AnnouncementResponse])
async def list_announcements(
    skip: int = 0,
    limit: int = 50,
    target_audience: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List announcements. Filter by target_audience if provided.
    """
    query = select(Announcement)

    if target_audience:
        query = query.where(
            or_(
                Announcement.target_audience == target_audience,
                Announcement.target_audience == "all"
            )
        )

    query = query.order_by(Announcement.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    announcement: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new announcement. Admin or teacher can create.
    """
    db_announcement = Announcement(
        school_id=current_user.school_id,
        title=announcement.title,
        body=announcement.body,
        target_audience=announcement.target_audience,
        publish_at=announcement.publish_at,
        created_by_id=current_user.id,
    )
    db.add(db_announcement)
    await db.commit()
    await db.refresh(db_announcement)
    return db_announcement


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific announcement by ID.
    """
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    announcement = result.scalar_one_or_none()

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return announcement


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: int,
    announcement_update: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update an announcement. Admin only.
    """
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    db_announcement = result.scalar_one_or_none()

    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    update_data = announcement_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_announcement, field, value)

    await db.commit()
    await db.refresh(db_announcement)
    return db_announcement


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete an announcement. Admin only.
    """
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    db_announcement = result.scalar_one_or_none()

    if not db_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    await db.delete(db_announcement)
    await db.commit()


# ============= Message Endpoints =============

@router.get("/messages", response_model=List[MessageResponse])
async def list_messages(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get received messages for the current user.
    """
    query = select(Message).where(Message.recipient_id == current_user.id)

    if unread_only:
        query = query.where(Message.is_read == False)

    query = query.order_by(Message.sent_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a direct message to another user.
    """
    # Verify recipient exists
    recipient_result = await db.execute(select(User).where(User.id == message.recipient_id))
    recipient = recipient_result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    db_message = Message(
        sender_id=current_user.id,
        recipient_id=message.recipient_id,
        subject=message.subject,
        body=message.body,
        sent_at=datetime.utcnow(),
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message


@router.get("/messages/sent", response_model=List[MessageResponse])
async def list_sent_messages(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get sent messages for the current user.
    """
    query = select(Message).where(Message.sender_id == current_user.id)
    query = query.order_by(Message.sent_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/messages/{message_id}/read", response_model=MessageResponse)
async def mark_message_as_read(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a message as read.
    """
    result = await db.execute(
        select(Message).where(
            and_(
                Message.id == message_id,
                Message.recipient_id == current_user.id
            )
        )
    )
    db_message = result.scalar_one_or_none()

    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")

    db_message.is_read = True
    db_message.read_at = datetime.utcnow()

    await db.commit()
    await db.refresh(db_message)
    return db_message


@router.get("/messages/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the count of unread messages for the current user.
    """
    result = await db.execute(
        select(Message).where(
            and_(
                Message.recipient_id == current_user.id,
                Message.is_read == False
            )
        )
    )
    messages = result.scalars().all()
    return {"unread_count": len(messages)}
