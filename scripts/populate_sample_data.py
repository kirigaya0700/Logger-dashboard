#!/usr/bin/env python3
"""
Script to populate sample data for DevLog application
"""
import os
import sys
sys.path.append('/app/backend')

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, date, timedelta
import uuid
import random

# Database connection
mongo_url = "mongodb://localhost:27017"
client = AsyncIOMotorClient(mongo_url)
db = client["test_database"]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_sample_data():
    """Create sample users and daily logs"""
    print("🚀 Creating sample data for DevLog...")
    
    # Create sample manager
    manager_id = str(uuid.uuid4())
    manager = {
        "id": manager_id,
        "username": "sarah_manager",
        "email": "sarah@company.com",
        "role": "manager",
        "password_hash": pwd_context.hash("Demo123!"),
        "manager_id": None,
        "created_at": datetime.utcnow()
    }
    
    # Create sample developers
    developers = []
    dev_names = [
        ("john_dev", "john@company.com", "John"),
        ("alice_dev", "alice@company.com", "Alice"),
        ("bob_dev", "bob@company.com", "Bob"),
        ("emma_dev", "emma@company.com", "Emma")
    ]
    
    for username, email, name in dev_names:
        dev_id = str(uuid.uuid4())
        developer = {
            "id": dev_id,
            "username": username,
            "email": email,
            "role": "developer",
            "password_hash": pwd_context.hash("Demo123!"),
            "manager_id": manager_id,
            "created_at": datetime.utcnow()
        }
        developers.append(developer)
    
    # Insert users
    await db.users.insert_one(manager)
    await db.users.insert_many(developers)
    print(f"✅ Created 1 manager and {len(developers)} developers")
    
    # Create daily logs for the past 30 days
    daily_logs = []
    feedbacks = []
    notifications = []
    
    for i in range(30):
        log_date = date.today() - timedelta(days=i)
        
        for dev in developers:
            # Skip some days randomly to make it more realistic
            if random.random() < 0.2:  # 20% chance to skip a day
                continue
                
            # Generate random tasks for each developer
            tasks = []
            num_tasks = random.randint(2, 5)
            
            task_templates = [
                ("Implemented authentication system", 3.5),
                ("Fixed bug in user dashboard", 1.5),
                ("Code review for PR #123", 0.5),
                ("Updated API documentation", 2.0),
                ("Optimized database queries", 2.5),
                ("Refactored user interface components", 4.0),
                ("Added unit tests for payment module", 2.0),
                ("Resolved production issue", 1.0),
                ("Implemented new feature: dark mode", 3.0),
                ("Performance optimization", 2.5),
                ("Security audit and fixes", 3.5),
                ("Database migration script", 1.5),
                ("Integration with third-party API", 4.5),
                ("Mobile responsiveness improvements", 2.0),
                ("Error handling improvements", 1.5)
            ]
            
            total_time = 0
            for _ in range(num_tasks):
                task_desc, base_time = random.choice(task_templates)
                time_spent = round(base_time + random.uniform(-0.5, 1.0), 1)
                if time_spent < 0.5:
                    time_spent = 0.5
                    
                tasks.append({
                    "description": task_desc,
                    "time_spent": time_spent,
                    "completed": random.choice([True, True, True, False])  # 75% completed
                })
                total_time += time_spent
            
            # Generate random mood (slightly biased towards positive)
            mood = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 25, 35, 25])[0]
            
            # Generate blockers occasionally
            blocker_options = [
                None,
                "Waiting for API documentation from external team",
                "Environment setup issues",
                "Blocked by code review process",
                "Dependency on another team's work",
                "Network connectivity issues"
            ]
            blockers = random.choices(blocker_options, weights=[70, 6, 6, 6, 6, 6])[0]
            
            log_id = str(uuid.uuid4())
            daily_log = {
                "id": log_id,
                "user_id": dev["id"],
                "date": log_date.isoformat(),
                "tasks": tasks,
                "total_time": round(total_time, 1),
                "mood": mood,
                "blockers": blockers,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            daily_logs.append(daily_log)
            
            # Add feedback from manager occasionally (30% chance)
            if random.random() < 0.3:
                feedback_messages = [
                    "Great work on the authentication system! Very clean implementation.",
                    "Good progress today. Please make sure to add more tests for the new features.",
                    "Excellent problem-solving on the production issue. Well done!",
                    "Thanks for the thorough code review. Your feedback was valuable.",
                    "Nice work on the API optimization. The performance improvements are noticeable.",
                    "Keep up the good work! Your consistency is impressive.",
                    "Good job handling the client requirements. Clear communication!",
                    "The documentation updates are very helpful. Thank you!"
                ]
                
                feedback_id = str(uuid.uuid4())
                feedback = {
                    "id": feedback_id,
                    "log_id": log_id,
                    "manager_id": manager_id,
                    "feedback_text": random.choice(feedback_messages),
                    "created_at": datetime.utcnow()
                }
                feedbacks.append(feedback)
                
                # Create notification for developer about feedback
                notif_id = str(uuid.uuid4())
                notification = {
                    "id": notif_id,
                    "user_id": dev["id"],
                    "message": f"New feedback from sarah_manager on your {log_date} log",
                    "type": "feedback",
                    "read": random.choice([True, False]),
                    "created_at": datetime.utcnow()
                }
                notifications.append(notification)
    
    # Insert daily logs
    if daily_logs:
        await db.daily_logs.insert_many(daily_logs)
    print(f"✅ Created {len(daily_logs)} daily logs")
    
    # Insert feedback
    if feedbacks:
        await db.feedback.insert_many(feedbacks)
    print(f"✅ Created {len(feedbacks)} feedback entries")
    
    # Insert notifications
    if notifications:
        await db.notifications.insert_many(notifications)
    
    # Add welcome notifications for all users
    welcome_notifications = []
    for user in [manager] + developers:
        notif_id = str(uuid.uuid4())
        welcome_notification = {
            "id": notif_id,
            "user_id": user["id"],
            "message": f"Welcome to DevLog, {user['username']}! Start logging your daily work.",
            "type": "info",
            "read": False,
            "created_at": datetime.utcnow()
        }
        welcome_notifications.append(welcome_notification)
    
    # Insert notifications
    all_notifications = welcome_notifications + notifications
    if all_notifications:
        try:
            await db.notifications.insert_many(all_notifications, ordered=False)
            print(f"✅ Created {len(all_notifications)} notifications")
        except Exception as e:
            print(f"⚠️ Some notifications may have been created (error: {str(e)[:100]}...)")
    
    print("\n🎉 Sample data creation completed!")
    print("\n📋 Login Credentials:")
    print("Manager:")
    print("  Username: sarah_manager")
    print("  Password: Demo123!")
    print("\nDevelopers:")
    for username, _, _ in dev_names:
        print(f"  Username: {username}")
        print(f"  Password: Demo123!")
    
    return manager, developers

async def clear_existing_data():
    """Clear existing sample data"""
    print("🧹 Clearing existing data...")
    
    # List of sample usernames to remove
    sample_usernames = ["sarah_manager", "john_dev", "alice_dev", "bob_dev", "emma_dev"]
    
    # Get user IDs
    users = await db.users.find({"username": {"$in": sample_usernames}}).to_list(1000)
    user_ids = [user["id"] for user in users]
    
    if user_ids:
        # Delete related data
        await db.daily_logs.delete_many({"user_id": {"$in": user_ids}})
        await db.feedback.delete_many({"manager_id": {"$in": user_ids}})
        await db.notifications.delete_many({"user_id": {"$in": user_ids}})
        await db.users.delete_many({"id": {"$in": user_ids}})
        print(f"✅ Removed data for {len(users)} sample users")
    else:
        print("ℹ️ No existing sample data found")

async def main():
    """Main function"""
    try:
        await clear_existing_data()
        await create_sample_data()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())