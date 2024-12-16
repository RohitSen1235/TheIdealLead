from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, DBUser
from services.auth import get_password_hash
from config import settings

# Create database engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def create_test_user():
    db = SessionLocal()
    try:
        # Check if test user already exists
        test_user = db.query(DBUser).filter(DBUser.email == "test@example.com").first()
        if test_user:
            print("Test user already exists")
            return

        # Create test user
        test_user = DBUser(
            email="test@example.com",
            name="Test User",
            company="Test Company",
            hashed_password=get_password_hash("testpass123"),
            credits=100
        )
        db.add(test_user)
        db.commit()
        print("Test user created successfully")
    except Exception as e:
        print(f"Error creating test user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
