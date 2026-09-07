from bloomerp.models.project_management.todo import Todo
from bloomerp.permissions.definition import AccessRule, BloomerpPermission, RowPolicyRuleCondition, RowPolicyRuleContent
from bloomerp.permissions.manager import PolicyManager
from bloomerp.tests.base import (
    BloomerpDetailViewTestCase,
    ExpectedResult,
    RequestSetup,
    ModelRequestSetup,
)


class TestBloomerpDeleteView(BloomerpDetailViewTestCase):
    view_name = 'delete'
    model = Todo
    
    def _give_access_to_normal_user(self, setup:RequestSetup):
        policy = PolicyManager.create_policy(
            model_or_content_type=Todo,
            access_rule=AccessRule(
                row_permissions=[
                    RowPolicyRuleContent(
                        permissions=[BloomerpPermission.DELETE],
                        conditions=[
                            RowPolicyRuleCondition(
                                field='__all__'
                            )
                        ]
                    )
                ],
                field_permissions={}
            ),
            global_permissions=BloomerpPermission.DELETE
        )
        PolicyManager.assign(policy, self.normal_user)
        
    
    def get_test_object(self):
        return Todo.objects.create(
            title="Hello"
        )
    
    def get_request_setups(self) -> list[RequestSetup]:
        
        self.normal_user.is_staff = True
        self.normal_user.save()
        
        return [
            RequestSetup(
                name="Accessible by admin user",
                method="GET",
                user=self.admin_user,
                expected=ExpectedResult(200)
            ),
            RequestSetup(
                name="Not accessible by regular user",
                method="GET",
                user=self.normal_user,
                expected=ExpectedResult(403)
            ),
            RequestSetup(
                name="Accessible by regular user with the right perm",
                method="GET",
                user=self.normal_user,
                expected=ExpectedResult(200),
                prepare=self._give_access_to_normal_user
            ),
            RequestSetup(
                name="Object get's deleted",
                method="POST",
                user=self.admin_user,
                expected=ExpectedResult(
                    status_code=302,
                    response_validators=[
                        lambda _: Todo.objects.count() == 0 
                    ]
                )
            ),
            RequestSetup(
                name="Normal user can't delete",
                method="POST",
                user=self.normal_user,
                expected=ExpectedResult(
                    status_code=403,
                    response_validators=[
                        lambda _: Todo.objects.count() == 1 
                    ]
                )
            ),
            
        ]
