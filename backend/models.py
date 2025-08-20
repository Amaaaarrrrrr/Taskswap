from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)  # increased length
    role = db.Column(db.String(20), default="user")
    skills = db.Column(db.String(255))
    rating = db.Column(db.Float, default=0.0)
    avatar_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    # Tasks created by user
    tasks_created = db.relationship(
        "Task",
        foreign_keys="Task.created_by",
        back_populates="creator"
    )

    # Tasks assigned to user
    tasks_assigned = db.relationship(
        "Task",
        foreign_keys="Task.assigned_to",
        back_populates="assignee"
    )

    # Swap requests made by user
    swap_requests = db.relationship(
        "SwapRequest",
        foreign_keys="SwapRequest.requester_id",
        back_populates="requester"
    )

    # Reviews written by user
    reviews_written = db.relationship(
        "Review",
        foreign_keys="Review.reviewer_id",
        back_populates="reviewer"
    )

    # Reviews received by user
    reviews_received = db.relationship(
        "Review",
        foreign_keys="Review.reviewee_id",
        back_populates="reviewee"
    )

    # -----------------------------
    # Admin check helper
    # -----------------------------
    def is_admin(self):
        return self.role.lower() == 'admin'

    def serialize(self):
            return {
                "id": self.id,
                "name": self.name,
                "email": self.email,
                "skills": self.skills,
                "rating": self.rating,
                "avatar_url": self.avatar_url,
                # Only include task IDs to avoid recursion
                "tasks_created": [task.id for task in self.tasks_created],
                "tasks_assigned": [task.id for task in self.tasks_assigned]
            }


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(50), default='open')  # open, assigned, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="tasks_created"
    )

    assignee = db.relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="tasks_assigned"
    )

    swap_requests = db.relationship(
        "SwapRequest",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    reviews = db.relationship(
        "Review",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    def serialize(self):
            return {
                "id": self.id,
                "title": self.title,
                "description": self.description,
                "category": self.category,
                "status": self.status,
                "created_by": self.created_by,
                "assigned_to": self.assigned_to,
                "creator": {
                    "id": self.creator.id,
                    "name": self.creator.name
                } if self.creator else None,
                "assignee": {
                    "id": self.assignee.id,
                    "name": self.assignee.name
                } if self.assignee else None,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat()
            }

class SwapRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    task = db.relationship("Task", back_populates="swap_requests")
    requester = db.relationship("User", back_populates="swap_requests")

    def serialize(self):
        return {
            "id": self.id,
            "task": self.task.serialize() if self.task else None,
            "requester": self.requester.serialize() if self.requester else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    reviewer = db.relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_written")
    reviewee = db.relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")
    task = db.relationship("Task", back_populates="reviews")

    def serialize(self):
        return {
            "id": self.id,
            "reviewer": self.reviewer.serialize() if self.reviewer else None,
            "reviewee": self.reviewee.serialize() if self.reviewee else None,
            "task": self.task.serialize() if self.task else None,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }
