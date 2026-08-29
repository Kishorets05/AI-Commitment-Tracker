"""
Database operations for users and commitments using MongoDB.
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def parse_deadline(deadline_val) -> Optional[datetime]:
    """Helper to safely parse deadline values into naive datetime objects."""
    if not deadline_val:
        return None
    if isinstance(deadline_val, datetime):
        return deadline_val
    try:
        return datetime.fromisoformat(deadline_val)
    except Exception:
        try:
            return datetime.strptime(deadline_val, "%Y-%m-%dT%H:%M")
        except Exception:
            return None


class Database:
    """Database manager for users and commitments using MongoDB."""

    def __init__(self):
        # Support fallback as requested by configuration instructions
        self.uri = os.environ.get("MONGODB_URI") or os.environ.get("MONGODB_CONNECTION_STRING")
        self.db_name = os.environ.get("MONGODB_DB_NAME") or os.environ.get("MONGODB_DATABASE_NAME") or "AI_Commitment_Tracker"

        if not self.uri:
            # Fallback to local default if not specified
            self.uri = "mongodb://localhost:27017/"

        self.client = None
        self.db = None
        self.users = None
        self.commitments = None
        self.connection_error = None

        try:
            # Connect to MongoDB with timeout
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
            self.db = self.client[self.db_name]
            self.users = self.db["users"]
            self.commitments = self.db["commitments"]

            # Trigger connection check
            self.client.admin.command('ping')

            # Initialize indexes
            self._init_indexes()
        except Exception as e:
            self.connection_error = str(e)
            print(f"MongoDB connection error: {e}")

    def _init_indexes(self):
        """Add sensible indexes for frequently queried fields."""
        if self.connection_error:
            return
        try:
            # Unique index on username
            self.users.create_index([("username", ASCENDING)], unique=True)

            # Indexes on commitments
            self.commitments.create_index([("user_id", ASCENDING)])
            self.commitments.create_index([("user_id", ASCENDING), ("deadline", ASCENDING)])
            self.commitments.create_index([("user_id", ASCENDING), ("status", ASCENDING)])
            self.commitments.create_index([("user_id", ASCENDING), ("priority", ASCENDING)])
        except Exception as e:
            print(f"Failed to create indexes: {e}")

    # --------------------------------------------------
    # User operations
    # --------------------------------------------------
    def create_user(self, username: str, password_hash: str) -> Optional[str]:
        """Create a new user with username and password hash."""
        if self.connection_error:
            return None
        try:
            user_doc = {
                "username": username,
                "password_hash": password_hash,
                "created_at": datetime.now().isoformat()
            }
            result = self.users.insert_one(user_doc)
            return str(result.inserted_id)
        except DuplicateKeyError:
            print(f"Username '{username}' already exists.")
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Fetch user by username."""
        if self.connection_error:
            return None
        try:
            user = self.users.find_one({"username": username})
            if user:
                user["id"] = str(user["_id"])
                return user
            return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None

    # --------------------------------------------------
    # Status Synchronization
    # --------------------------------------------------
    def sync_overdue_commitments(self, user_oid: ObjectId):
        """Synchronize overdue commitments based on system date/time."""
        if self.connection_error:
            return
        try:
            now = datetime.now()
            # Find all pending commitments with deadlines for this user
            query = {
                "user_id": user_oid,
                "status": "Pending",
                "deadline": {"$ne": None}
            }
            pending_commits = list(self.commitments.find(query))

            for commit in pending_commits:
                deadline_dt = parse_deadline(commit.get("deadline"))
                if deadline_dt and deadline_dt < now:
                    self.commitments.update_one(
                        {"_id": commit["_id"]},
                        {"$set": {
                            "status": "Overdue",
                            "updated_at": now.isoformat()
                        }}
                    )
        except Exception as e:
            print(f"Error synchronizing overdue commitments: {e}")

    # --------------------------------------------------
    # Analytics
    # --------------------------------------------------
    def get_user_analytics(self, user_id: str) -> Dict[str, int]:
        """Calculate counts for commitments belonging to the user using aggregation."""
        if self.connection_error:
            return {"total": 0, "pending": 0, "completed": 0, "overdue": 0, "high": 0, "medium": 0, "low": 0}

        try:
            user_oid = ObjectId(user_id)
            # Sync first to ensure overdue commitments are updated in database
            self.sync_overdue_commitments(user_oid)

            pipeline = [
                {"$match": {"user_id": user_oid}},
                {"$facet": {
                    "by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                    ],
                    "by_priority": [
                        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
                    ],
                    "total": [
                        {"$count": "count"}
                    ]
                }}
            ]

            results = list(self.commitments.aggregate(pipeline))
            
            # Default values
            counts = {
                "total": 0,
                "pending": 0,
                "completed": 0,
                "overdue": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }

            if not results:
                return counts

            facet = results[0]
            
            # Total
            if facet.get("total") and len(facet["total"]) > 0:
                counts["total"] = facet["total"][0]["count"]

            # Statuses
            for item in facet.get("by_status", []):
                status_name = item["_id"]
                if status_name in ["Pending", "Completed", "Overdue"]:
                    counts[status_name.lower()] = item["count"]

            # Priorities
            for item in facet.get("by_priority", []):
                priority_name = item["_id"]
                if priority_name in ["High", "Medium", "Low"]:
                    counts[priority_name.lower()] = item["count"]

            return counts
        except Exception as e:
            print(f"Error calculating analytics: {e}")
            return {"total": 0, "pending": 0, "completed": 0, "overdue": 0, "high": 0, "medium": 0, "low": 0}

    # --------------------------------------------------
    # Commitment operations
    # --------------------------------------------------
    def create_commitment(
        self,
        user_id: str,
        subject: str,
        description: str = "",
        deadline: Optional[str] = None,
        status: str = "Pending",
        priority: str = "Medium",
        priority_source: str = "ML"
    ) -> Optional[str]:
        """Create a new commitment document."""
        if self.connection_error:
            return None
        try:
            now = datetime.now().isoformat()
            doc = {
                "user_id": ObjectId(user_id),
                "subject": subject,
                "description": description,
                "deadline": deadline,
                "status": status,
                "priority": priority,
                "priority_source": priority_source,
                "created_at": now,
                "updated_at": now
            }
            result = self.commitments.insert_one(doc)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating commitment: {e}")
            return None

    def get_user_commitments(
        self,
        user_id: str,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        search_text: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve commitments for a user, with sorting, filtering, and search."""
        if self.connection_error:
            return []

        try:
            user_oid = ObjectId(user_id)
            # Sync status automatically before querying
            self.sync_overdue_commitments(user_oid)

            query = {"user_id": user_oid}
            if status:
                query["status"] = status
            if priority:
                query["priority"] = priority
            if search_text:
                query["$or"] = [
                    {"subject": {"$regex": search_text, "$options": "i"}},
                    {"description": {"$regex": search_text, "$options": "i"}}
                ]

            commitments = list(self.commitments.find(query))

            # Map _id to id string for frontend template compatibility
            for commit in commitments:
                commit["id"] = str(commit["_id"])

            # Sort commitments
            priority_map = {"High": 1, "Medium": 2, "Low": 3}
            if sort_by == "priority_high_first":
                # Sort by priority High (1) -> Medium (2) -> Low (3), then by deadline ASC
                commitments.sort(key=lambda x: (
                    priority_map.get(x.get("priority", "Medium"), 4),
                    x.get("deadline") or "9999-12-31T23:59:59"
                ))
            elif sort_by == "deadline_desc":
                # Latest deadline first (non-deadlines placed last)
                commitments.sort(key=lambda x: x.get("created_at") or "", reverse=True)
                commitments.sort(key=lambda x: x.get("deadline") or "", reverse=True)
            elif sort_by == "created_desc":
                # Recently created first
                commitments.sort(key=lambda x: x.get("created_at") or "", reverse=True)
            else:
                # Default: deadline_asc (nearest deadline first)
                commitments.sort(key=lambda x: x.get("created_at") or "", reverse=True)
                commitments.sort(key=lambda x: x.get("deadline") or "9999-12-31T23:59:59")

            return commitments
        except Exception as e:
            print(f"Error getting user commitments: {e}")
            return []

    def get_urgent_commitments(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Retrieve high-priority pending commitments whose deadline has not yet passed."""
        if self.connection_error:
            return []

        try:
            user_oid = ObjectId(user_id)
            # Sync status automatically before querying
            self.sync_overdue_commitments(user_oid)

            now_iso = datetime.now().isoformat()
            query = {
                "user_id": user_oid,
                "status": "Pending",
                "priority": "High",
                "deadline": {"$ne": None, "$gte": now_iso}
            }

            commitments = list(self.commitments.find(query).sort("deadline", ASCENDING).limit(limit))

            # Map _id to id string
            for commit in commitments:
                commit["id"] = str(commit["_id"])

            return commitments
        except Exception as e:
            print(f"Error getting urgent commitments: {e}")
            return []

    def update_commitment_status(self, commitment_id: str, user_id: str, status: str) -> bool:
        """Update a commitment status if it belongs to the logged-in user."""
        if self.connection_error:
            return False

        try:
            result = self.commitments.update_one(
                {"_id": ObjectId(commitment_id), "user_id": ObjectId(user_id)},
                {"$set": {
                    "status": status,
                    "updated_at": datetime.now().isoformat()
                }}
            )
            return result.matched_count > 0
        except Exception as e:
            print(f"Error updating commitment status: {e}")
            return False

    def update_commitment_priority(self, commitment_id: str, user_id: str, priority: str) -> bool:
        """Manually override priority and set priority_source to 'Manual'."""
        if self.connection_error:
            return False

        try:
            result = self.commitments.update_one(
                {"_id": ObjectId(commitment_id), "user_id": ObjectId(user_id)},
                {"$set": {
                    "priority": priority,
                    "priority_source": "Manual",
                    "updated_at": datetime.now().isoformat()
                }}
            )
            return result.matched_count > 0
        except Exception as e:
            print(f"Error updating commitment priority: {e}")
            return False

    def update_commitment(
        self,
        commitment_id: str,
        user_id: str,
        subject: str = None,
        description: str = None,
        deadline: str = None,
        status: str = None,
        priority: str = None,
        priority_source: str = None
    ) -> bool:
        """Perform generic commitment updates."""
        if self.connection_error:
            return False

        try:
            update_fields = {}
            for key, val in {
                "subject": subject,
                "description": description,
                "deadline": deadline,
                "status": status,
                "priority": priority,
                "priority_source": priority_source
            }.items():
                if val is not None:
                    update_fields[key] = val

            if not update_fields:
                return False

            update_fields["updated_at"] = datetime.now().isoformat()

            result = self.commitments.update_one(
                {"_id": ObjectId(commitment_id), "user_id": ObjectId(user_id)},
                {"$set": update_fields}
            )
            return result.matched_count > 0
        except Exception as e:
            print(f"Error updating commitment: {e}")
            return False

    def delete_commitment(self, commitment_id: str, user_id: str) -> bool:
        """Delete a commitment if it belongs to the logged-in user."""
        if self.connection_error:
            return False

        try:
            result = self.commitments.delete_one(
                {"_id": ObjectId(commitment_id), "user_id": ObjectId(user_id)}
            )
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting commitment: {e}")
            return False
