from datetime import datetime, timedelta
from sqlalchemy import func
from flask import Blueprint, jsonify
from config.helpers.helpers import super_admin_required
from config.extensions.database_config import db
import logging
from flasgger import swag_from
from models.users import User, UserStatus, UserRole, MessageRole, ChatMessage, ChatSession
from config.limit_config.limiter import limiter


logger = logging.getLogger(__name__)

stat_bp = Blueprint("stat", __name__)

@limiter.limit("30 per minute")
@stat_bp.get("/super-admin/stats")
@super_admin_required
@swag_from({
    "tags": ["Super Admin statstics"],
    "summary": "Dashboard statistics",
    "description": (
        "Returns summary statistics, chart data and recent activity "
        "for the Super Admin dashboard."
    ),
    "security": [
        {
            "Bearer": []
        }
    ],
    "responses": {
        200: {
            "description": "Dashboard statistics retrieved successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "cards": {
                        "type": "object",
                        "properties": {
                            "total_users": {
                                "type": "integer",
                                "example": 125
                            },
                            "registered_users": {
                                "type": "integer",
                                "example": 97
                            },
                            "anonymous_users": {
                                "type": "integer",
                                "example": 28
                            },
                            "active_users": {
                                "type": "integer",
                                "example": 80
                            },
                            "inactive_users": {
                                "type": "integer",
                                "example": 17
                            },
                            "admins": {
                                "type": "integer",
                                "example": 4
                            },
                            "total_sessions": {
                                "type": "integer",
                                "example": 314
                            },
                            "total_messages": {
                                "type": "integer",
                                "example": 5243
                            },
                            "user_messages": {
                                "type": "integer",
                                "example": 2617
                            },
                            "assistant_messages": {
                                "type": "integer",
                                "example": 2580
                            },
                            "avg_messages_per_session": {
                                "type": "number",
                                "example": 16.7
                            },
                            "avg_sessions_per_user": {
                                "type": "number",
                                "example": 2.5
                            }
                        }
                    },
                    "charts": {
                        "type": "object",
                        "properties": {
                            "registrations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {
                                            "type": "string",
                                            "example": "2026-08-01"
                                        },
                                        "count": {
                                            "type": "integer",
                                            "example": 7
                                        }
                                    }
                                }
                            },
                            "sessions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {
                                            "type": "string",
                                            "example": "2026-08-01"
                                        },
                                        "count": {
                                            "type": "integer",
                                            "example": 23
                                        }
                                    }
                                }
                            },
                            "messages": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {
                                            "type": "string",
                                            "example": "2026-08-01"
                                        },
                                        "count": {
                                            "type": "integer",
                                            "example": 412
                                        }
                                    }
                                }
                            },
                            "roles": {
                                "type": "object",
                                "properties": {
                                    "super_admin": {
                                        "type": "integer",
                                        "example": 1
                                    },
                                    "admin": {
                                        "type": "integer",
                                        "example": 4
                                    },
                                    "user": {
                                        "type": "integer",
                                        "example": 120
                                    }
                                }
                            },
                            "status": {
                                "type": "object",
                                "properties": {
                                    "active": {
                                        "type": "integer",
                                        "example": 80
                                    },
                                    "inactive": {
                                        "type": "integer",
                                        "example": 17
                                    },
                                    "anonymous": {
                                        "type": "integer",
                                        "example": 28
                                    }
                                }
                            },
                            "message_roles": {
                                "type": "object",
                                "properties": {
                                    "user": {
                                        "type": "integer",
                                        "example": 2617
                                    },
                                    "assistant": {
                                        "type": "integer",
                                        "example": 2580
                                    },
                                    "system": {
                                        "type": "integer",
                                        "example": 46
                                    }
                                }
                            }
                        }
                    },
                    "recent": {
                        "type": "object",
                        "properties": {
                            "users": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {
                                            "type": "integer",
                                            "example": 23
                                        },
                                        "name": {
                                            "type": "string",
                                            "example": "John Doe"
                                        },
                                        "email": {
                                            "type": "string",
                                            "example": "john@example.com"
                                        },
                                        "role": {
                                            "type": "string",
                                            "example": "user"
                                        },
                                        "created_at": {
                                            "type": "string",
                                            "example": "2026-08-01T12:15:22"
                                        }
                                    }
                                }
                            },
                            "sessions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "chat_id": {
                                            "type": "string",
                                            "example": "7a6ecf3b-b4f3-4705-bb43-95a76cb8ebea"
                                        },
                                        "user": {
                                            "type": "string",
                                            "example": "John Doe"
                                        },
                                        "created_at": {
                                            "type": "string",
                                            "example": "2026-08-01T13:10:55"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "Failed to retrieve dashboard statistics.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False
                    },
                    "message": {
                        "type": "string",
                        "example": "Unable to load dashboard statistics."
                    }
                }
            }
        }
    }
})
def super_admin_stats():
    try:
        today = datetime.utcnow()
        last_7_days = today - timedelta(days=6)
        last_30_days = today - timedelta(days=29)

        total_users = User.query.count()

        registered_users = User.query.filter(
            User.is_registered.is_(True)
        ).count()

        anonymous_users = User.query.filter(
            User.status == UserStatus.ANONYMOUS
        ).count()

        active_users = User.query.filter(
            User.status == UserStatus.ACTIVE
        ).count()

        inactive_users = User.query.filter(
            User.status == UserStatus.INACTIVE
        ).count()

        admins = User.query.filter(
            User.role == UserRole.ADMIN
        ).count()

        total_sessions = ChatSession.query.count()

        total_messages = ChatMessage.query.count()

        user_messages = ChatMessage.query.filter(
            ChatMessage.role == MessageRole.USER
        ).count()

        assistant_messages = ChatMessage.query.filter(
            ChatMessage.role == MessageRole.ASSISTANT
        ).count()

        avg_messages_per_session = round(
            total_messages / total_sessions, 2
        ) if total_sessions else 0

        avg_sessions_per_user = round(
            total_sessions / total_users, 2
        ) if total_users else 0

        registrations = (
            db.session.query(
                func.date(User.created_at),
                func.count(User.id)
            )
            .filter(User.created_at >= last_30_days)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at))
            .all()
        )

        registration_chart = [
            {
                "date": str(date),
                "count": count
            }
            for date, count in registrations
        ]

        sessions = (
            db.session.query(
                func.date(ChatSession.created_at),
                func.count(ChatSession.id)
            )
            .filter(ChatSession.created_at >= last_30_days)
            .group_by(func.date(ChatSession.created_at))
            .order_by(func.date(ChatSession.created_at))
            .all()
        )

        session_chart = [
            {
                "date": str(date),
                "count": count
            }
            for date, count in sessions
        ]

        messages = (
            db.session.query(
                func.date(ChatMessage.created_at),
                func.count(ChatMessage.id)
            )
            .filter(ChatMessage.created_at >= last_30_days)
            .group_by(func.date(ChatMessage.created_at))
            .order_by(func.date(ChatMessage.created_at))
            .all()
        )

        message_chart = [
            {
                "date": str(date),
                "count": count
            }
            for date, count in messages
        ]

        role_chart = {
            "super_admin": User.query.filter(
                User.role == UserRole.SUPER_ADMIN
            ).count(),

            "admin": admins,

            "user": User.query.filter(
                User.role == UserRole.USER
            ).count()
        }

        status_chart = {
            "active": active_users,
            "inactive": inactive_users,
            "anonymous": anonymous_users
        }


        message_role_chart = {
            "user": user_messages,
            "assistant": assistant_messages,
            "system": ChatMessage.query.filter(
                ChatMessage.role == MessageRole.SYSTEM
            ).count()
        }

        recent_users = [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "created_at": user.created_at.isoformat()
            }
            for user in User.query.order_by(
                User.created_at.desc()
            ).limit(5)
        ]

        recent_sessions = [
            {
                "chat_id": session.chat_id,
                "user": session.user.name,
                "created_at": session.created_at.isoformat()
            }
            for session in ChatSession.query.order_by(
                ChatSession.created_at.desc()
            ).limit(5)
        ]

        return jsonify({
            "success": True,

            "cards": {
                "total_users": total_users,
                "registered_users": registered_users,
                "anonymous_users": anonymous_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "admins": admins,
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "avg_messages_per_session": avg_messages_per_session,
                "avg_sessions_per_user": avg_sessions_per_user
            },

            "charts": {
                "registrations": registration_chart,
                "sessions": session_chart,
                "messages": message_chart,
                "roles": role_chart,
                "status": status_chart,
                "message_roles": message_role_chart
            },

            "recent": {
                "users": recent_users,
                "sessions": recent_sessions
            }

        }), 200

    except Exception as e:
        logger.exception(str(e))

        return jsonify({
            "success": False,
            "message": "Unable to load dashboard statistics."
        }), 500