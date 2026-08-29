"""
Seeding script to populate the MongoDB database with realistic users and commitments.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from werkzeug.security import generate_password_hash

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from webapp.database.database import Database
from webapp.backend.priority_predictor import predict_priority_with_source


def seed_data():
    print("=" * 60)
    print("AI COMMITMENT TRACKER - DATABASE SEEDER")
    print("=" * 60)

    # 1. Initialize Database
    db = Database()
    if db.connection_error:
        print(f"FAILED: Connection error: {db.connection_error}")
        return

    print("[OK] Connected to MongoDB.")

    # 2. Define 12 Seeded Users
    usernames = [
        "alice_green", "bob_miller", "charlie_brown", "david_white",
        "emma_black", "fiona_gold", "george_silver", "hannah_blue",
        "ian_red", "julia_orange", "kevin_yellow", "laura_violet"
    ]
    password = "Password123!"
    pw_hash = generate_password_hash(password)

    # Clear existing data for these seeded users to prevent duplicate clutter
    print("Cleaning old seeded data...")
    db.users.delete_many({"username": {"$in": usernames}})
    
    # We will fetch and clean commitments for these users after creating/fetching them
    print("Seeding users...")
    user_ids = {}
    for uname in usernames:
        user_id = db.create_user(uname, pw_hash)
        if user_id:
            user_ids[uname] = user_id
            # Clean commitments for this user ID
            from bson.objectid import ObjectId
            db.commitments.delete_many({"user_id": ObjectId(user_id)})
            print(f"  - Created user: {uname} (ID: {user_id})")

    print(f"[OK] Seeded {len(user_ids)} users successfully.")

    # 3. Define 20 Realistic Commitments
    commitment_templates = [
        {
            "subject": "Submit Python coding assignment",
            "description": "Complete exercises on lists, dictionaries, and file handling.",
            "offset": timedelta(days=2),
            "status": "Pending"
        },
        {
            "subject": "Pay monthly internet bill",
            "description": "Pay Comcast bill online before the due date to avoid service fee.",
            "offset": timedelta(days=4),
            "status": "Pending"
        },
        {
            "subject": "Attend Project sprint planning",
            "description": "Alignment meeting with the development team on upcoming tasks.",
            "offset": timedelta(hours=3),
            "status": "Pending"
        },
        {
            "subject": "Finish reading AWS documentation",
            "description": "Review EC2, S3, and RDS service limits and pricing models.",
            "offset": timedelta(days=-1),
            "status": "Pending"
        },
        {
            "subject": "Team review session for UI mockups",
            "description": "Provide feedback on styleguide, glassmorphism design, and contrast.",
            "offset": timedelta(days=-2),
            "status": "Completed"
        },
        {
            "subject": "Schedule dentist appointment",
            "description": "Bi-annual cleaning and checkup at Downtown Dental clinic.",
            "offset": timedelta(days=10),
            "status": "Pending"
        },
        {
            "subject": "Buy groceries for weekly meal planning",
            "description": "Purchase organic eggs, milk, whole wheat bread, avocado, and chicken.",
            "offset": timedelta(days=1),
            "status": "Pending"
        },
        {
            "subject": "Review code pull request #145",
            "description": "Approve frontend React refactoring changes and merge branch.",
            "offset": timedelta(hours=6),
            "status": "Pending"
        },
        {
            "subject": "Pay rent for apartment 4B",
            "description": "Transfer funds to landlord account before the 1st of the month.",
            "offset": timedelta(days=3),
            "status": "Pending"
        },
        {
            "subject": "Submit monthly expense report",
            "description": "Submit gas receipts and travel receipts to accounting team.",
            "offset": timedelta(days=-3),
            "status": "Pending"
        },
        {
            "subject": "Update LinkedIn profile summary",
            "description": "Revise summary bio, add recent projects, and upload new avatar.",
            "offset": timedelta(days=14),
            "status": "Pending"
        },
        {
            "subject": "Fix login page authentication bug",
            "description": "Resolve Werkzeug password checking syntax error in backend controller.",
            "offset": timedelta(hours=-2),
            "status": "Completed"
        },
        {
            "subject": "Prepare slides for stakeholder review",
            "description": "Create powerpoint presentation for the quarterly results meeting.",
            "offset": timedelta(days=2),
            "status": "Pending"
        },
        {
            "subject": "Buy birthday gift for mother",
            "description": "Order flower bouquet and customized necklace from Etsy.",
            "offset": timedelta(days=5),
            "status": "Pending"
        },
        {
            "subject": "Car maintenance service appointment",
            "description": "Schedule oil change, tire rotation, and brake pads inspection.",
            "offset": timedelta(days=7),
            "status": "Pending"
        },
        {
            "subject": "Write blog post on FastAPI vs Flask",
            "description": "Draft comparative analysis covering performance, scaling, and async.",
            "offset": timedelta(days=8),
            "status": "Pending"
        },
        {
            "subject": "Attend job interview with TechCorp",
            "description": "Technical screening covering algorithms, SQL, and database caching.",
            "offset": timedelta(hours=2),
            "status": "Pending"
        },
        {
            "subject": "Renew vehicle registration document",
            "description": "Submit emissions report online and pay state DMV processing fee.",
            "offset": timedelta(days=-5),
            "status": "Pending"
        },
        {
            "subject": "Discuss marketing strategy with team",
            "description": "Review Q3 conversion funnels, SEO rankings, and newsletter metrics.",
            "offset": timedelta(days=-1),
            "status": "Completed"
        },
        {
            "subject": "Backup local project directory",
            "description": "Export current codebase zip to external hard drive and cloud storage.",
            "offset": timedelta(hours=-8),
            "status": "Completed"
        }
    ]

    # 4. Seed 5-6 commitments for each user
    print("Seeding commitments...")
    now = datetime.now()
    total_seeded = 0

    for uname, uid in user_ids.items():
        # Randomly choose 5 or 6 commitments from the templates
        num_commitments = random.choice([5, 6])
        selected_templates = random.sample(commitment_templates, num_commitments)

        for tmpl in selected_templates:
            deadline_dt = now + tmpl["offset"]
            text = f"{tmpl['subject']} {tmpl['description']}".strip()
            
            # Dynamically calculate priority & source via Predictor rules
            priority, source = predict_priority_with_source(text, deadline_dt)

            success = db.create_commitment(
                user_id=uid,
                subject=tmpl["subject"],
                description=tmpl["description"],
                deadline=deadline_dt.isoformat(),
                status=tmpl["status"],
                priority=priority,
                priority_source=source
            )
            if success:
                total_seeded += 1

        print(f"  - Seeded {num_commitments} commitments for user '{uname}'")

    print("\n" + "=" * 60)
    print("DATABASE SEEDING SUCCESSFUL!")
    print(f"Total Seeded Users: {len(user_ids)}")
    print(f"Total Seeded Commitments: {total_seeded}")
    print("All password credentials set to: 'Password123!'")
    print("=" * 60)


if __name__ == "__main__":
    seed_data()
