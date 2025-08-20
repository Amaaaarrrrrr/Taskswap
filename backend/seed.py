from app import app, db
from models import User, Task, SwapRequest, Review
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed():
    with app.app_context():
        # ⚠️ Clears the database
        db.drop_all()
        db.create_all()

        # --- Create Users ---
        admin = User(
            name="admin",
            email="admin@example.com",
            password_hash=generate_password_hash("admin123"),
            role="admin"
        )
        alice = User(
            name="Alice",
            email="alice@example.com",
            password_hash=generate_password_hash("password123"),
            skills="Python, React",
            rating=4.5
        )
        bob = User(
            name="Bob",
            email="bob@example.com",
            password_hash=generate_password_hash("password123"),
            skills="Graphic Design, UX",
            rating=4.2
        )
        charlie = User(
            name="Charlie",
            email="charlie@example.com",
            password_hash=generate_password_hash("password123"),
            skills="Marketing, SEO",
            rating=4.8
        )

        db.session.add_all([alice, bob, charlie, admin])
        db.session.commit()

        # --- Create Tasks ---
        task1 = Task(
            title="Build a portfolio website",
            description="Create a portfolio website with React for Alice.",
            category="Development",
            creator=alice
        )
        task2 = Task(
            title="Design a poster",
            description="Need a poster for a local event.",
            category="Design",
            creator=bob,
            assignee=charlie
        )
        task3 = Task(
            title="SEO optimization",
            description="Improve SEO for company blog.",
            category="Marketing",
            creator=charlie
        )

        db.session.add_all([task1, task2, task3])
        db.session.commit()

        # --- Create Swap Requests ---
        swap1 = SwapRequest(
            task=task3,
            requester=alice,
            status="pending"
        )
        swap2 = SwapRequest(
            task=task2,
            requester=charlie,
            status="accepted"
        )

        db.session.add_all([swap1, swap2])
        db.session.commit()

        # --- Create Reviews ---
        review1 = Review(
            reviewer=alice,
            reviewee=charlie,
            task=task2,
            rating=5.0,
            comment="Great work on the poster!"
        )
        review2 = Review(
            reviewer=charlie,
            reviewee=alice,
            task=task1,
            rating=4.8,
            comment="Portfolio website looks amazing!"
        )

        db.session.add_all([review1, review2])
        db.session.commit()

        print("✅ Database seeded successfully!")

if __name__ == "__main__":
    seed()
