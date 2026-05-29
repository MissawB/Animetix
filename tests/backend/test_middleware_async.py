import pytest
import asyncio
from django.contrib.auth.models import User
from django.test import RequestFactory
import sys
from animetix.middleware import UserTrackingMiddleware, UserTierMiddleware, user_id_var, user_tier_var


@pytest.mark.django_db
class TestMiddlewareAsync:
    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_user_tracking_middleware_sync(self):
        def get_response(request):
            assert user_id_var.get() == self.user.id
            return "OK"

        middleware = UserTrackingMiddleware(get_response)
        request = self.factory.get('/')
        request.user = self.user
        
        response = middleware(request)
        assert response == "OK"
        assert user_id_var.get() is None

    @pytest.mark.asyncio
    async def test_user_tracking_middleware_async(self):
        async def get_response(request):
            assert user_id_var.get() == self.user.id
            return "OK"

        middleware = UserTrackingMiddleware(get_response)
        request = self.factory.get('/')
        request.user = self.user
        
        # Django's middleware __call__ handles the dispatch if we implemented it that way
        response = middleware(request)
        if asyncio.iscoroutine(response):
            response = await response
            
        assert response == "OK"
        assert user_id_var.get() is None

    def test_user_tier_middleware_sync(self):
        def get_response(request):
            assert user_tier_var.get() == 'free'
            assert request.user_tier == 'free'
            return "OK"

        middleware = UserTierMiddleware(get_response)
        request = self.factory.get('/')
        request.user = self.user
        
        response = middleware(request)
        assert response == "OK"
        assert user_tier_var.get() == 'free' # default is free

    @pytest.mark.asyncio
    async def test_user_tier_middleware_async(self):
        async def get_response(request):
            assert user_tier_var.get() == 'free'
            assert request.user_tier == 'free'
            return "OK"

        middleware = UserTierMiddleware(get_response)
        request = self.factory.get('/')
        request.user = self.user
        
        response = middleware(request)
        if asyncio.iscoroutine(response):
            response = await response
            
        assert response == "OK"
        assert user_tier_var.get() == 'free'
