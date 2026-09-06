
from dataclasses import dataclass
from typing import Literal, Optional

from django.urls import reverse
from bloomerp.models.users.user import AbstractBloomerpUser
from bloomerp.tests.base import BaseBloomerpTestCaseWithModels

@dataclass
class ExpectedResult:
    status_code:int
    

@dataclass
class RequestSetup:
    method:Literal["GET", "POST"]
    user:AbstractBloomerpUser
    expected:ExpectedResult
    name:Optional[str] = None
    description:Optional[str] = None
    get_args:Optional[dict] = None
    post_args:Optional[dict] = None
    view_kwargs:Optional[dict] = None
    


class BaseBloomerpComponentTest(BaseBloomerpTestCaseWithModels):
    view_name:str
    
    def get_endpoint(
        view_name:str,
        kwargs:dict
    ) -> str:
        return reverse(
            viewname=view_name,
            kwargs=kwargs
        )
    
    def get_request_setups(self) -> list[RequestSetup]:
        pass
    
    def test_request_setups(self):
        """
        Tests every request setup
        """
        for setup in self.get_request_setups():
            self.client.login(
                setup.user
            )
            
            if setup.method == "GET":
                response = self.client.get(
                    path=self.get_endpoint(
                        self.view_name,
                        setup.view_kwargs
                    ),
                )
            
            self.client.logout()