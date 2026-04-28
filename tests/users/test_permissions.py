import pytest
from rest_framework import status


@pytest.mark.django_db
class TestRolePermissions:
    surveys_url = "/api/surveys/"

    def test_creator_can_create_survey(self, creator_client):
        response = creator_client.post(self.surveys_url, {"title": "Мой опрос"})
        assert response.status_code == status.HTTP_201_CREATED

    def test_taker_cannot_create_survey(self, taker_client):
        response = taker_client.post(self.surveys_url, {"title": "Чужой опрос"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_create_survey(self, api_client):
        response = api_client.post(self.surveys_url, {"title": "Без токена"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_taker_can_see_available_surveys(self, taker_client, survey):
        response = taker_client.get("/api/surveys/available/")
        assert response.status_code == status.HTTP_200_OK

    def test_creator_cannot_see_available_surveys(self, creator_client):
        # available/ — только для takers
        response = creator_client.get("/api/surveys/available/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_creator_cannot_answer_survey(self, creator_client, full_survey):
        response = creator_client.get(f"/api/surveys/{full_survey.pk}/next-question/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
