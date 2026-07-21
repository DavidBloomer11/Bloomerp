from rest_framework import status
from bloomerp.models.access_control.policy import Policy
from bloomerp.serializers.access_control import (
    PolicySerializer,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db import transaction

from bloomerp.router import router
from bloomerp.views.api.generic.base import BaseModelApiView


class PolicyViewSet(BaseModelApiView):
    """
    API endpoint for managing access control policies.

    Supports:
    - list
    - retrieve
    - create (nested row_policy + field_policy)
    """

    queryset = (
        Policy.objects
        .select_related("row_policy", "field_policy")
        .prefetch_related(
            "row_policy__rules__permissions",
        )
    )

    serializer_class = PolicySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        """
        Optionally restrict policies based on the user.
        For now: return all policies.
        """
        return self.queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a Policy with nested RowPolicy, RowPolicyRules and FieldPolicy.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        policy = serializer.save(
            created_by=request.user,
            updated_by=request.user,
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            self.get_serializer(policy).data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


@router.register(
    path="",
    route_type="api_model",
    models=Policy,
)
class PolicyListAPIView(PolicyViewSet):
    actions = {
        "get": "list",
        "post": "create",
    }


@router.register(
    path="",
    route_type="api_detail",
    models=Policy,
)
class PolicyDetailAPIView(PolicyViewSet):
    actions = {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
