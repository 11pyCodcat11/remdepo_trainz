from django.utils.deprecation import MiddlewareMixin
from asgiref.sync import async_to_sync
from .repository import get_user_by_id
from .sqlalchemy_base import AsyncSessionLocal


class SQLAlchemyAuthMiddleware(MiddlewareMixin):
    """Подмешивает request.user из SQLAlchemy, вместо стандартного Django User."""

    def process_request(self, request):
        user_id = request.session.get("user_id")
        if not user_id:
            request.user = None
            return

        async def _get_user():
            async with AsyncSessionLocal() as session:
                return await get_user_by_id(session, user_id)

        request.user = async_to_sync(_get_user)()
