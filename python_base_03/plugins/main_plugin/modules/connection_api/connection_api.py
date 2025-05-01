import os
import json
from tools.logger.custom_logging import custom_log, log_function_call
from utils.config.config import Config
from core.managers.redis_manager import RedisManager
from core.managers.jwt_manager import JWTManager, TokenType
from core.managers.database_manager import DatabaseManager
from tools.error_handling import ErrorHandler
from datetime import datetime, timedelta
import time
import uuid
import logging
from flask import request
from typing import Dict, Any

class ConnectionAPI:
    def __init__(self, app_manager=None):
        """Initialize the ConnectionAPI with Redis and database connections."""
        self.registered_routes = []
        self.app = None  # Reference to Flask app
        self.app_manager = app_manager  # Reference to AppManager if provided
        
        # Initialize database managers with different roles
        self.db_manager = DatabaseManager(role="read_write")  # For write operations
        self.analytics_db = DatabaseManager(role="read_only")  # For read operations
        self.admin_db = DatabaseManager(role="admin")  # For administrative tasks
        
        self.redis_manager = RedisManager()  # Initialize Redis manager
        self.jwt_manager = JWTManager()  # Initialize JWT manager
        self.error_handler = ErrorHandler()  # Initialize error handler
        self.logger = logging.getLogger(__name__)
        
        # Session management settings
        self.session_timeout = 3600  # 1 hour in seconds
        self.max_concurrent_sessions = 1  # Only one session allowed per user
        self.session_check_interval = 300  # 5 minutes in seconds

        # ✅ Ensure collections exist in the database
        self.initialize_database()

    def initialize(self, app):
        """Initialize the ConnectionAPI with a Flask app."""
        if not hasattr(app, "add_url_rule"):
            raise RuntimeError("ConnectionAPI requires a valid Flask app instance.")
        self.app = app
        
        # Register the refresh token endpoint
        self.register_route("/auth/refresh", self.refresh_token_endpoint, methods=["POST"])

    def initialize_database(self):
        """Ensure required collections exist in the database."""
        custom_log("⚙️ Initializing database collections...")
        self._create_users_collection()
        custom_log("✅ Database collections verified.")

    def _create_users_collection(self):
        """Create users collection with proper indexes."""
        try:
            # Create users collection with indexes
            self.admin_db.db.users.create_index("email", unique=True)
            self.admin_db.db.users.create_index("username")
            self.admin_db.db.users.create_index("created_at")
            custom_log("✅ Users collection and indexes created")
        except Exception as e:
            custom_log(f"❌ Error creating users collection: {e}")
            raise

    def get_user_by_email(self, email):
        """Get user by email with proper error handling."""
        try:
            return self.analytics_db.find_one("users", {"email": email})
        except Exception as e:
            self.logger.error(f"Error getting user by email: {e}")
            return None

    def create_user(self, username, email, hashed_password):
        """Create a new user with proper error handling."""
        try:
            user_data = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            user_id = self.db_manager.insert("users", user_data)
            return self.get_user_by_email(email)
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            raise

    def delete_user(self, user_id):
        """Delete a user and all associated data with proper error handling."""
        try:
            # Delete user data from all collections
            self.db_manager.delete("users", {"_id": user_id})
            self.db_manager.delete("user_sessions", {"user_id": user_id})
            self.db_manager.delete("user_tokens", {"user_id": user_id})
            
            # Invalidate any cached user data
            self._invalidate_caches(f"user:{user_id}")
            custom_log(f"✅ User {user_id} and associated data deleted")
        except Exception as e:
            self.logger.error(f"Error deleting user: {e}")
            raise

    def fetch_from_db(self, collection, query, as_dict=False):
        """Execute a query and cache results in Redis."""
        try:
            # Validate query
            if not query or not isinstance(query, dict):
                raise ValueError("Invalid query format")
                
            # Create cache key based on query
            cache_key = f"query:{hash(str(query))}"
            
            # Try to get from Redis cache first
            try:
                cached_result = self.redis_manager.get(cache_key)
                if cached_result:
                    custom_log(f"✅ Retrieved query result from Redis cache")
                    return cached_result
            except Exception as e:
                self.logger.warning(f"Cache retrieval failed: {e}")
            
            # Execute query
            result = self.analytics_db.find(collection, query)
            
            # Cache the result
            try:
                self.redis_manager.set(cache_key, result, expire=300)  # Cache for 5 minutes
                custom_log(f"✅ Cached query result in Redis")
            except Exception as e:
                self.logger.warning(f"Cache storage failed: {e}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise

    def execute_query(self, collection, query, data=None):
        """Execute a write operation and invalidate relevant caches."""
        try:
            if data:
                # Update operation
                result = self.db_manager.update(collection, query, data)
            else:
                # Delete operation
                result = self.db_manager.delete(collection, query)
            
            # Invalidate relevant caches
            self._invalidate_caches(collection)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise

    def _invalidate_caches(self, collection):
        """Invalidate relevant Redis caches based on the collection."""
        try:
            # Invalidate collection-specific caches
            pattern = f"query:*{collection}*"
            keys = self.redis_manager.redis.keys(pattern)
            for key in keys:
                self.redis_manager.delete(key)
            
            # Invalidate user data cache if users collection
            if collection == "users":
                pattern = "user:*"
                keys = self.redis_manager.redis.keys(pattern)
                for key in keys:
                    self.redis_manager.delete(key)
            
            custom_log("✅ Relevant caches invalidated")
        except Exception as e:
            self.logger.error(f"Error invalidating caches: {e}")
            raise

    def _create_session(self, user_id: int, username: str, email: str) -> dict:
        """Create a new session for a user."""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Prepare session data
            session_data = {
                'user_id': user_id,
                'username': username,
                'email': email,
                'created_at': datetime.utcnow(),
                'last_active': datetime.utcnow()
            }
            
            # Store session in database
            self.db_manager.insert("user_sessions", session_data)
            
            # Store session in Redis for quick access
            self.redis_manager.set(f"session:{session_id}", json.dumps(session_data), expire=3600)
            
            self.logger.info(f"Created new session {session_id} for user {username}")
            return {'session_id': session_id, **session_data}
            
        except Exception as e:
            self.logger.error(f"Error creating session: {e}")
            raise

    def _remove_session(self, session_id: str, user_id: int) -> bool:
        """Remove a session from both database and cache."""
        try:
            # Remove from database
            self.db_manager.delete("user_sessions", {"session_id": session_id})
            
            # Remove from Redis
            self.redis_manager.delete(f"session:{session_id}")
            
            self.logger.info(f"Removed session {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing session: {e}")
            return False
            
    def check_active_sessions(self, user_id: int) -> bool:
        """Check if a user has any active sessions."""
        try:
            # Check database for active sessions
            sessions = self.analytics_db.find("user_sessions", {"user_id": user_id})
            return len(sessions) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking active sessions: {e}")
            return False

    def refresh_token_endpoint(self):
        """Endpoint to refresh user tokens."""
        try:
            data = request.get_json()
            if not data or "refresh_token" not in data:
                return {"error": "Refresh token is required"}, 400
                
            refresh_token = data["refresh_token"]
            result, status_code = self.refresh_user_tokens(refresh_token)
            
            if status_code != 200:
                return result, status_code
                
            return result, 200
            
        except Exception as e:
            self.logger.error(f"Error in refresh token endpoint: {e}")
            return {"error": "Internal server error"}, 500

    def create_user_tokens(self, user_data):
        """Create access and refresh tokens for a user."""
        try:
            custom_log(f"🔐 Starting token creation for user ID: {user_data['_id']}")
            
            # Create access token
            access_token = self.jwt_manager.create_token(
                user_data,
                TokenType.ACCESS,
                expires_in=3600  # 1 hour
            )

            # Create refresh token
            refresh_token = self.jwt_manager.create_token(
                user_data,
                TokenType.REFRESH,
                expires_in=604800  # 7 days
            )

            # Store tokens in database
            token_data = {
                "user_id": user_data["_id"],
                "access_token": access_token,
                "refresh_token": refresh_token,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=7)
            }
            self.db_manager.insert("user_tokens", token_data)

            # Store tokens in Redis for quick access
            self.redis_manager.set(
                f"access_token:{user_data['_id']}",
                access_token,
                expire=3600
            )
            self.redis_manager.set(
                f"refresh_token:{user_data['_id']}",
                refresh_token,
                expire=604800
            )

            # Create session
            session_data = self._create_session(
                user_data['_id'],
                user_data['username'],
                user_data['email']
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "session_id": session_data['session_id']
            }

        except Exception as e:
            custom_log(f"❌ Error creating tokens: {e}")
            raise

    def validate_access_token(self, token):
        """Validate an access token."""
        try:
            return self.jwt_manager.validate_token(token, TokenType.ACCESS)
        except Exception as e:
            custom_log(f"❌ Error validating access token: {e}")
            return None

    def refresh_user_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh user's access and refresh tokens."""
        try:
            # Verify refresh token
            user_data = self.jwt_manager.verify_token(refresh_token)
            if not user_data or "user_id" not in user_data:
                self.logger.error("Invalid refresh token: Token verification failed")
                return {"error": "Invalid refresh token"}, 401

            # Get user from database
            user = self.get_user_by_email(user_data["email"])
            if not user:
                self.logger.error(f"User not found for email: {user_data['email']}")
                return {"error": "User not found"}, 404

            # Generate new tokens
            new_tokens = self.create_user_tokens(user)
            if not new_tokens:
                self.logger.error("Failed to generate new tokens")
                return {"error": "Failed to generate new tokens"}, 500

            return {"tokens": new_tokens}, 200

        except Exception as e:
            self.logger.error(f"Error refreshing tokens: {e}")
            return {"error": "Failed to refresh tokens"}, 500

    def revoke_user_tokens(self, user_id: int) -> bool:
        """Revoke all tokens and sessions for a user."""
        try:
            custom_log(f"🟢 Revoking tokens for user ID: {user_id}")
            
            # Delete all sessions
            self.db_manager.delete("user_sessions", {"user_id": user_id})
            
            # Delete all tokens
            self.db_manager.delete("user_tokens", {"user_id": user_id})
            
            # Clear Redis caches
            self.redis_manager.delete(f"access_token:{user_id}")
            self.redis_manager.delete(f"refresh_token:{user_id}")
            self.redis_manager.delete(f"user:{user_id}")
            
            custom_log(f"✅ Successfully revoked all tokens and cleared data for user {user_id}")
            return True
            
        except Exception as e:
            custom_log(f"❌ Error revoking tokens: {e}")
            return False

    def dispose(self):
        """Clean up resources."""
        try:
            # Close database connections
            self.db_manager.close()
            self.analytics_db.close()
            self.admin_db.close()
            
            # Close Redis connection
            self.redis_manager.dispose()
            
            custom_log("✅ All connections closed")
        except Exception as e:
            custom_log(f"❌ Error during disposal: {e}")
