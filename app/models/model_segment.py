from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Table,Index
from sqlalchemy.orm import relationship
from app.db.database import Base

# Table associative pour lier les invités aux segments
# segment_guests = Table(
#     "segment_guests",
#     Base.metadata,
#     Column("segment_id", Integer, ForeignKey("segments.id"), primary_key=True),
#     Column("guest_id", Integer, ForeignKey("guests.id"), primary_key=True)
# )

class Segment(Base):
    __tablename__ = "segments"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False, index=True)
    duration = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    technical_notes = Column(Text, nullable=True)
    

    position = Column(Integer, nullable=False, default=0)  # Nouvelle colonne

    # show_id = Column(Integer, ForeignKey("shows.id"), nullable=False, index=True)
    # show = relationship("Show", back_populates="segments")
      # Clé étrangère vers Show
    show_id = Column(Integer, ForeignKey("shows.id", ondelete="CASCADE"))

    # Relation inverse vers Show
    show = relationship("Show", back_populates="segments")
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, index=True)

    # guests = relationship("Guest", secondary=segment_guests, back_populates="segments")

    # Relation avec les invités via la table SegmentGuest
    # guests = relationship("Guest", secondary="segment_guests", back_populates="segments")
    # guests = relationship("Guest", secondary="segment_guests", back_populates="segments", cascade="all")

    # Relation plusieurs-à-plusieurs avec Guest via SegmentGuest
    guests = relationship("Guest", secondary="segment_guests", back_populates="segments")
    __table_args__ = (
        Index("ix_segment_title_type", "title", "type"),
    )
