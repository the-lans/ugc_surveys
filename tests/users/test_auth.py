import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
class TestRegister:
    url = "/api/auth/register/"

    def test_register_creator(self, api_client):
        response = api_client.post(
            self.url,
            {
                "username": "newcreator",
                "password": "strongpass1",
                "role": "creator",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["role"] == "creator"
        assert "access" in data
        assert "refresh" in data
        assert User.objects.filter(username="newcreator").exists()

    def test_register_taker(self, api_client):
        response = api_client.post(
            self.url,
            {
                "username": "newtaker",
                "password": "strongpass1",
                "role": "taker",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_default_role_is_taker(self, api_client):
        response = api_client.post(
            self.url,
            {
                "username": "norole",
                "password": "strongpass1",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["role"] == "taker"

    @pytest.mark.parametrize("bad_role", ["admin", "superuser", ""])
    def test_invalid_role_rejected(self, api_client, bad_role):
        response = api_client.post(
            self.url,
            {
                "username": "u",
                "password": "strongpass1",
                "role": bad_role,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_short_password_rejected(self, api_client):
        response = api_client.post(
            self.url,
            {
                "username": "u",
                "password": "short",
                "role": "taker",
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestJWT:
    token_url = "/api/auth/token/"
    refresh_url = "/api/auth/token/refresh/"

    def test_obtain_token(self, api_client, creator_user):
        response = api_client.post(
            self.token_url,
            {
                "username": "creator",
                "password": "testpass123",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.json()
        assert "refresh" in response.json()

    def test_wrong_password(self, api_client, creator_user):
        response = api_client.post(
            self.token_url,
            {
                "username": "creator",
                "password": "wrongpass",
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, api_client, creator_user):
        tokens = api_client.post(
            self.token_url,
            {
                "username": "creator",
                "password": "testpass123",
            },
        ).json()
        response = api_client.post(self.refresh_url, {"refresh": tokens["refresh"]})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.json()
