"""
User Service Layer
==================

This module provides a comprehensive service layer for user management,
handling all user types (customer, provider, admin, developer) with
role-based access control and profile management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union

from flask import current_app
from sqlalchemy.exc import IntegrityError

from src.models.admin import Admin
from src.models.user import CustomerProfile, ProviderProfile, User, db
from src.utils.error_handling import ServiceError
from src.utils.validation import validate_email, validate_password


class UserService:
    """Comprehensive user management service"""

    @staticmethod
    def get_user_by_id(user_id: int, user_type: str = "user") -> Optional[Dict]:
        """Get user by ID with profile information"""
        try:
            if user_type == "admin":
                admin = Admin.query.get(user_id)
                if admin:
                    return {
                        "user": admin.to_dict(),
                        "user_type": "admin",
                        "profile": None,
                    }
            else:
                user = User.query.get(user_id)
                if user:
                    profile = None
                    if user.user_type == "customer":
                        profile = CustomerProfile.query.filter_by(
                            user_id=user.id
                        ).first()
                    elif user.user_type == "provider":
                        profile = ProviderProfile.query.filter_by(
                            user_id=user.id
                        ).first()

                    return {
                        "user": user.to_dict(),
                        "user_type": user.user_type,
                        "profile": profile.to_dict() if profile else None,
                    }

            return None

        except Exception as e:
            current_app.logger.error(f"Error getting user {user_id}: {e}")
            raise ServiceError(f"Failed to retrieve user: {str(e)}")

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Get user by email with profile information"""
        try:
            email = email.lower().strip()

            # Check regular users first
            user = User.query.filter_by(email=email).first()
            if user:
                profile = None
                if user.user_type == "customer":
                    profile = CustomerProfile.query.filter_by(user_id=user.id).first()
                elif user.user_type == "provider":
                    profile = ProviderProfile.query.filter_by(user_id=user.id).first()

                return {
                    "user": user.to_dict(),
                    "user_type": user.user_type,
                    "profile": profile.to_dict() if profile else None,
                }

            # Check admin users
            admin = Admin.query.filter_by(email=email).first()
            if admin:
                return {"user": admin.to_dict(), "user_type": "admin", "profile": None}

            return None

        except Exception as e:
            current_app.logger.error(f"Error getting user by email {email}: {e}")
            raise ServiceError(f"Failed to retrieve user: {str(e)}")

    @staticmethod
    def create_user(user_data: Dict) -> Dict:
        """Create a new user with profile"""
        try:
            # Validate required fields
            required_fields = [
                "email",
                "password",
                "first_name",
                "last_name",
                "user_type",
            ]
            for field in required_fields:
                if field not in user_data or not user_data[field]:
                    raise ServiceError(f"Missing required field: {field}")

            email = user_data["email"].lower().strip()
            user_type = user_data["user_type"]

            # Validate inputs
            if not validate_email(email):
                raise ServiceError("Invalid email format")

            if not validate_password(user_data["password"]):
                raise ServiceError("Password must be at least 8 characters long")

            if user_type not in ["customer", "provider"]:
                raise ServiceError("Invalid user type")

            # Check if user already exists
            if UserService.get_user_by_email(email):
                raise ServiceError("Email already registered")

            # Create user
            user = User(
                email=email,
                first_name=user_data["first_name"].strip(),
                last_name=user_data["last_name"].strip(),
                user_type=user_type,
                phone=user_data.get("phone", "").strip(),
                street_address=user_data.get("street_address", "").strip(),
                city=user_data.get("city", "").strip(),
                state=user_data.get("state", "").strip(),
                postcode=user_data.get("postcode", "").strip(),
                is_active=True,
                is_verified=False,
            )
            user.set_password(user_data["password"])

            db.session.add(user)
            db.session.flush()  # Get user ID

            # Create profile based on user type
            if user_type == "customer":
                profile = CustomerProfile(
                    user_id=user.id,
                    preferred_contact_method=user_data.get(
                        "preferred_contact_method", "email"
                    ),
                    notification_preferences=user_data.get(
                        "notification_preferences", {}
                    ),
                )
            else:  # provider
                profile = ProviderProfile(
                    user_id=user.id,
                    business_name=user_data.get("business_name", "").strip(),
                    abn=user_data.get("abn", "").strip(),
                    years_experience=user_data.get("years_experience", 0),
                    hourly_rate=user_data.get("hourly_rate", 0.0),
                    bio=user_data.get("bio", "").strip(),
                    skills=user_data.get("skills", []),
                    availability=user_data.get("availability", {}),
                )

            db.session.add(profile)
            db.session.commit()

            current_app.logger.info(f"Created new {user_type}: {email}")

            return {
                "user": user.to_dict(),
                "user_type": user_type,
                "profile": profile.to_dict(),
            }

        except IntegrityError:
            db.session.rollback()
            raise ServiceError("Email already registered")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user: {e}")
            raise ServiceError(f"Failed to create user: {str(e)}")

    @staticmethod
    def update_user_profile(
        user_id: int, profile_data: Dict, user_type: str = "user"
    ) -> Dict:
        """Update user profile information"""
        try:
            if user_type == "admin":
                admin = Admin.query.get(user_id)
                if not admin:
                    raise ServiceError("Admin not found")

                # Update admin fields
                updatable_fields = ["first_name", "last_name", "phone"]
                for field in updatable_fields:
                    if field in profile_data:
                        setattr(admin, field, profile_data[field])

                db.session.commit()

                return {"user": admin.to_dict(), "user_type": "admin", "profile": None}

            else:
                user = User.query.get(user_id)
                if not user:
                    raise ServiceError("User not found")

                # Update user fields
                updatable_fields = [
                    "first_name",
                    "last_name",
                    "phone",
                    "street_address",
                    "city",
                    "state",
                    "postcode",
                    "bio",
                ]
                for field in updatable_fields:
                    if field in profile_data:
                        setattr(user, field, profile_data[field])

                # Update profile based on user type
                profile = None
                if user.user_type == "customer":
                    profile = CustomerProfile.query.filter_by(user_id=user.id).first()
                    if profile:
                        profile_fields = [
                            "preferred_contact_method",
                            "notification_preferences",
                        ]
                        for field in profile_fields:
                            if field in profile_data:
                                setattr(profile, field, profile_data[field])

                elif user.user_type == "provider":
                    profile = ProviderProfile.query.filter_by(user_id=user.id).first()
                    if profile:
                        profile_fields = [
                            "business_name",
                            "abn",
                            "years_experience",
                            "hourly_rate",
                            "bio",
                            "skills",
                            "availability",
                        ]
                        for field in profile_fields:
                            if field in profile_data:
                                setattr(profile, field, profile_data[field])

                db.session.commit()

                return {
                    "user": user.to_dict(),
                    "user_type": user.user_type,
                    "profile": profile.to_dict() if profile else None,
                }

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user profile {user_id}: {e}")
            raise ServiceError(f"Failed to update profile: {str(e)}")

    @staticmethod
    def change_password(
        user_id: int, current_password: str, new_password: str, user_type: str = "user"
    ) -> bool:
        """Change user password"""
        try:
            if not validate_password(new_password):
                raise ServiceError("New password must be at least 8 characters long")

            if user_type == "admin":
                admin = Admin.query.get(user_id)
                if not admin:
                    raise ServiceError("Admin not found")

                if not admin.check_password(current_password):
                    raise ServiceError("Current password is incorrect")

                admin.set_password(new_password)
                db.session.commit()

                current_app.logger.info(f"Admin {user_id} changed password")
                return True

            else:
                user = User.query.get(user_id)
                if not user:
                    raise ServiceError("User not found")

                if not user.check_password(current_password):
                    raise ServiceError("Current password is incorrect")

                user.set_password(new_password)
                db.session.commit()

                current_app.logger.info(f"User {user_id} changed password")
                return True

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error changing password for user {user_id}: {e}")
            raise ServiceError(f"Failed to change password: {str(e)}")

    @staticmethod
    def toggle_user_status(user_id: int, admin_id: int) -> Dict:
        """Toggle user active status (admin only)"""
        try:
            # Verify admin permissions
            admin = Admin.query.get(admin_id)
            if not admin or not admin.is_active:
                raise ServiceError("Unauthorized: Admin access required")

            user = User.query.get(user_id)
            if not user:
                raise ServiceError("User not found")

            user.is_active = not user.is_active
            db.session.commit()

            status = "activated" if user.is_active else "deactivated"
            current_app.logger.info(f"Admin {admin_id} {status} user {user_id}")

            return {"user": user.to_dict(), "status": status}

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error toggling user status {user_id}: {e}")
            raise ServiceError(f"Failed to toggle user status: {str(e)}")

    @staticmethod
    def get_users_list(filters: Dict = None, page: int = 1, per_page: int = 20) -> Dict:
        """Get paginated list of users with filters"""
        try:
            query = User.query

            # Apply filters
            if filters:
                if "user_type" in filters:
                    query = query.filter(User.user_type == filters["user_type"])

                if "is_active" in filters:
                    query = query.filter(User.is_active == filters["is_active"])

                if "search" in filters and filters["search"]:
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        db.or_(
                            User.first_name.ilike(search_term),
                            User.last_name.ilike(search_term),
                            User.email.ilike(search_term),
                        )
                    )

            # Paginate
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            users = []
            for user in pagination.items:
                profile = None
                if user.user_type == "customer":
                    profile = CustomerProfile.query.filter_by(user_id=user.id).first()
                elif user.user_type == "provider":
                    profile = ProviderProfile.query.filter_by(user_id=user.id).first()

                users.append(
                    {
                        "user": user.to_dict(),
                        "profile": profile.to_dict() if profile else None,
                    }
                )

            return {
                "users": users,
                "pagination": {
                    "page": pagination.page,
                    "pages": pagination.pages,
                    "per_page": pagination.per_page,
                    "total": pagination.total,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                },
            }

        except Exception as e:
            current_app.logger.error(f"Error getting users list: {e}")
            raise ServiceError(f"Failed to retrieve users: {str(e)}")

    @staticmethod
    def verify_user_email(user_id: int) -> bool:
        """Mark user email as verified"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ServiceError("User not found")

            user.is_verified = True
            user.email_verified_at = datetime.utcnow()
            db.session.commit()

            current_app.logger.info(f"User {user_id} email verified")
            return True

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error verifying user email {user_id}: {e}")
            raise ServiceError(f"Failed to verify email: {str(e)}")

    @staticmethod
    def get_user_dashboard_data(user_id: int, user_type: str = "user") -> Dict:
        """Get dashboard data for user"""
        try:
            user_data = UserService.get_user_by_id(user_id, user_type)
            if not user_data:
                raise ServiceError("User not found")

            # Get user-specific dashboard data
            dashboard_data = {
                "user": user_data["user"],
                "profile": user_data["profile"],
                "user_type": user_data["user_type"],
            }

            # Add type-specific data
            if user_data["user_type"] == "customer":
                # Add customer-specific dashboard data
                dashboard_data.update(
                    {
                        "active_jobs": 0,  # TODO: Implement job counting
                        "completed_jobs": 0,
                        "total_spent": 0.0,
                        "recent_activity": [],
                    }
                )

            elif user_data["user_type"] == "provider":
                # Add provider-specific dashboard data
                dashboard_data.update(
                    {
                        "active_jobs": 0,  # TODO: Implement job counting
                        "completed_jobs": 0,
                        "total_earned": 0.0,
                        "rating": 0.0,
                        "recent_activity": [],
                    }
                )

            elif user_data["user_type"] == "admin":
                # Add admin-specific dashboard data
                dashboard_data.update(
                    {
                        "total_users": User.query.count(),
                        "total_providers": User.query.filter_by(
                            user_type="provider"
                        ).count(),
                        "total_customers": User.query.filter_by(
                            user_type="customer"
                        ).count(),
                        "active_jobs": 0,  # TODO: Implement job counting
                        "recent_activity": [],
                    }
                )

            return dashboard_data

        except Exception as e:
            current_app.logger.error(
                f"Error getting dashboard data for user {user_id}: {e}"
            )
            raise ServiceError(f"Failed to retrieve dashboard data: {str(e)}")


class RoleBasedAccessControl:
    """Role-based access control utilities"""

    PERMISSIONS = {
        "customer": [
            "view_own_profile",
            "edit_own_profile",
            "create_job",
            "view_own_jobs",
            "message_providers",
        ],
        "provider": [
            "view_own_profile",
            "edit_own_profile",
            "view_jobs",
            "apply_to_jobs",
            "message_customers",
            "manage_services",
        ],
        "admin": [
            "view_all_users",
            "edit_all_users",
            "view_all_jobs",
            "manage_platform",
            "access_admin_panel",
        ],
        "developer": [
            "view_all_users",
            "edit_all_users",
            "view_all_jobs",
            "manage_platform",
            "access_admin_panel",
            "access_dev_tools",
            "manage_system",
        ],
    }

    @staticmethod
    def has_permission(user_type: str, permission: str) -> bool:
        """Check if user type has specific permission"""
        return permission in RoleBasedAccessControl.PERMISSIONS.get(user_type, [])

    @staticmethod
    def get_user_permissions(user_type: str) -> List[str]:
        """Get all permissions for user type"""
        return RoleBasedAccessControl.PERMISSIONS.get(user_type, [])

    @staticmethod
    def can_access_resource(
        user_type: str, resource: str, action: str = "view"
    ) -> bool:
        """Check if user can access specific resource"""
        permission = f"{action}_{resource}"
        return RoleBasedAccessControl.has_permission(user_type, permission)

    @staticmethod
    def get_dashboard_route(user_type: str) -> str:
        """Get appropriate dashboard route for user type"""
        routes = {
            "customer": "/dashboard",
            "provider": "/provider-dashboard",
            "admin": "/admin-dashboard",
            "developer": "/dev-dashboard",
        }
        return routes.get(user_type, "/dashboard")
