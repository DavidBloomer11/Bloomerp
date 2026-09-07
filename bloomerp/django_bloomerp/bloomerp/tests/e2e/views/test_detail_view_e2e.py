from dataclasses import dataclass
from typing import Callable, Optional

from bloomerp.models.project_management.todo import Todo
from bloomerp.models.users.user import User

@dataclass
class Action:
    execute:Callable[[]]
    validator:Callable[[], bool]
    name:Optional[str] = None
    

@dataclass
class RequestSetup:
    name:str
    url:str
    actions:list[Action]
    auto_login:bool
    description:str
    user:Optional[User] = None

class BloomerpE2ETestCase:
    admin_user : User
    normal_user : User
    
    
    def go_to_page(self, url:str):
        pass
    
    def input_field(self, id:str, value:str):
        pass
    
    def press_button(self, label:str):
        pass
    
    

class TestDetailViewE2E(BloomerpE2ETestCase):
    
    def get_request_setups(self) -> list:
        obj = Todo.objects.create(
            title="Hello world"
        )
        
        return [
           RequestSetup(
               name="User sees auto generated fields",
               url="123",
               actions=[
                   Action(
                       execute=self.go_to_page(
                           obj.get_absolute_url()
                       ),
                   ),
                   Action(
                       execute=self.input_field(
                           "title",
                           "Hello world 2"
                       )
                   ),
                   Action(
                       execute=self.press_button(
                           "Save"
                       ),
                       validator=lambda : Todo.objects.get(id=obj.id).title == "Hello world 2"
                   )
               ],
               user=self.admin_user
           ) 
        ]
        