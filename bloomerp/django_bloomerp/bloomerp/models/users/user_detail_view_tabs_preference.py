from bloomerp.models.users.base_view_preference import BaseViewPreference
from django.db import models
from pydantic import BaseModel

class Tab(BaseModel):
    label: str
    url: str
    is_folder: bool
    


class UserDetailViewTabsPreference(BaseViewPreference):
    tabs = models.JSONField(
        
    )
    
    
    @classmethod
    def create_default_for_user(cls, user, **scope):
        return UserDetailViewTabsPreference.objects.create(
            user=user,
            content_type_id=scope.get("content_type_id"),
        )
    
