import contextvars

current_user_account = contextvars.ContextVar("current_user_account", default="GUEST")