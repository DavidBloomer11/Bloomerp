
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Optional

from django.http import HttpResponse
from django.urls import reverse
from bloomerp.models.users.user import AbstractBloomerpUser
from bloomerp.tests.base import BaseBloomerpTestCaseWithModels

ResponseValidator = Callable[[HttpResponse], bool]

@dataclass
class ExpectedResult:
    status_code:int = 200
    response_validators:Optional[ResponseValidator | list[ResponseValidator]] = None
    

@dataclass
class RequestSetup:
    method:Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"] = "GET"
    user:Optional[AbstractBloomerpUser] = None
    expected:ExpectedResult = field(default_factory=ExpectedResult)
    name:Optional[str] = None
    description:Optional[str] = None
    data:Optional[dict] = None
    query_params:Optional[dict] = None
    view_kwargs:Optional[dict] = None
    headers:Optional[dict] = None
    content_type:Optional[str] = None
    follow:bool = False
    


class BaseBloomerpComponentTest(BaseBloomerpTestCaseWithModels):
    view_name:str
    
    def get_endpoint(
        self,
        view_name:str,
        kwargs:Optional[dict]
    ) -> str:
        return reverse(
            viewname=view_name,
            kwargs=kwargs
        )
    
    def get_request_setups(self) -> list[RequestSetup]:
        raise NotImplementedError("Component tests must define request setups")
    
    def test_request_setups(self):
        """
        Tests every request setup
        """
        if type(self) is BaseBloomerpComponentTest:
            return

        for idx, setup in enumerate(self.get_request_setups(), start=1):
            try:
                if setup.user:
                    self.client.force_login(setup.user)
                else:
                    self.client.logout()

                request_kwargs = {
                    "path": self.get_endpoint(self.view_name, setup.view_kwargs),
                    "data": setup.data,
                    "query_params": setup.query_params,
                    "headers": setup.headers,
                    "follow": setup.follow,
                }
                if setup.content_type:
                    if setup.method in {"GET", "HEAD", "TRACE"}:
                        raise ValueError(f"{setup.method} requests do not support content_type")
                    request_kwargs["content_type"] = setup.content_type

                response = getattr(self.client, setup.method.lower())(**request_kwargs)

                self.assertEqual(
                    response.status_code,
                    setup.expected.status_code,
                    f"Unexpected status code for test case {idx}: {setup.name} \n {setup.description}"
                )
                    
                validators = setup.expected.response_validators
                if validators:
                    if callable(validators):
                        validators = [validators]
                    for validator in validators:
                        self.assertTrue(
                            validator(response),
                            f"Response validator {self._validator_name(validator)} failed for test case "
                            f"{idx}: {setup.name} \n {setup.description}"
                        )
            finally:
                self.client.logout()

    @staticmethod
    def _named_validator(name: str, validator: ResponseValidator) -> ResponseValidator:
        """Assign a descriptive name to a validator for assertion failure output."""
        validator.__name__ = name
        return validator

    @staticmethod
    def _validator_name(validator: ResponseValidator) -> str:
        """Return a readable name for a validator callable."""
        return getattr(validator, "__name__", type(validator).__name__)

    @staticmethod
    def contains_text(text: str) -> ResponseValidator:
        """Return a validator that passes when the response body contains text."""
        return BaseBloomerpComponentTest._named_validator(
            f"contains_text({text!r})",
            lambda response: text in response.content.decode(response.charset or "utf-8"),
        )

    @staticmethod
    def does_not_contain_text(text: str) -> ResponseValidator:
        """Return a validator that passes when the response body does not contain text."""
        return BaseBloomerpComponentTest._named_validator(
            f"does_not_contain_text({text!r})",
            lambda response: text not in response.content.decode(response.charset or "utf-8"),
        )

    @staticmethod
    def contains_div(div: str) -> ResponseValidator:
        """Return a validator that passes when the response HTML contains a div fragment."""
        return BaseBloomerpComponentTest._named_validator(
            f"contains_div({div!r})",
            BaseBloomerpComponentTest.contains_text(div),
        )

    @staticmethod
    def is_json() -> ResponseValidator:
        """Return a validator that passes when the response body is valid JSON."""
        def validator(response: HttpResponse) -> bool:
            try:
                response.json()
            except (TypeError, ValueError):
                return False
            return True
        return BaseBloomerpComponentTest._named_validator("is_json()", validator)

    @staticmethod
    def key_in_json(key: str) -> ResponseValidator:
        """Return a validator that passes when the top-level JSON object contains key."""
        def validator(response: HttpResponse) -> bool:
            try:
                payload = response.json()
            except (TypeError, ValueError):
                return False
            return isinstance(payload, dict) and key in payload
        return BaseBloomerpComponentTest._named_validator(f"key_in_json({key!r})", validator)

    @staticmethod
    def json_exact(expected_json: Any) -> ResponseValidator:
        """Return a validator that passes when the decoded JSON exactly equals expected_json."""
        def validator(response: HttpResponse) -> bool:
            try:
                return response.json() == expected_json
            except (TypeError, ValueError):
                return False
        return BaseBloomerpComponentTest._named_validator(f"json_exact({expected_json!r})", validator)

    @staticmethod
    def json_key_equals(key: str, expected_value: Any) -> ResponseValidator:
        """Return a validator that passes when a top-level JSON key has the expected value."""
        def validator(response: HttpResponse) -> bool:
            try:
                payload = response.json()
            except (TypeError, ValueError):
                return False
            return isinstance(payload, dict) and payload.get(key) == expected_value
        return BaseBloomerpComponentTest._named_validator(
            f"json_key_equals({key!r}, {expected_value!r})",
            validator,
        )

    @staticmethod
    def header_equals(name: str, expected_value: str) -> ResponseValidator:
        """Return a validator that passes when a response header exactly matches a value."""
        return BaseBloomerpComponentTest._named_validator(
            f"header_equals({name!r}, {expected_value!r})",
            lambda response: response.headers.get(name) == expected_value,
        )

    @staticmethod
    def redirects_to(url: str) -> ResponseValidator:
        """Return a validator that passes when the response redirects to url."""
        return BaseBloomerpComponentTest._named_validator(
            f"redirects_to({url!r})",
            lambda response: response.status_code in {301, 302, 303, 307, 308}
            and response.headers.get("Location") == url,
        )
    
    