


from functools import reduce
from operator import or_
from typing import Any

from django.db.models import Q, Model, QuerySet

from bloomerp.filters.lookups import LOOKUP_REGISTRY
from bloomerp.models.application_field import ApplicationField


class QuerysetFilterManager:
    
    def filter_queryset(self, model:Model, args:dict[str, Any]) -> QuerySet[Model]:
        q_conditions = self.create_q_conditions(model, args)
    
    def create_q_conditions(self, model:Model, args:dict[str, Any]) -> list[Q]:
        conditions = []
        
        for arg, value in args.items():
            sub_conditions = []
            for sub_condition in self.strip_args(arg, value):
                condition, value = sub_condition
                split = condition.split("__", maxsplit=1)[0]
                application_field = ApplicationField.get_for_model(model).filter(
                    field=split[0]
                )
                if len(split) == 1:
                    expression_id = ""
                else:
                    expression_id = split[1]
                
                lookup = LOOKUP_REGISTRY.get_lookup_by_id(
                    expression_id,
                    application_field
                )
                
                q = lookup.q_factory(application_field, condition, value)
                sub_conditions.append(q)
                
            conditions.append(reduce(or_, sub_conditions, Q()))
            
        return conditions
            
            
            
    def strip_args(self, arg:str, value:Any) -> list[tuple[str, Any]]:
        """Example:
        
        arg: first_name
        value: John
            -> [
                ("first_name", "bloomer")
            ]
            
        arg: first_name
        value: John||first_name=James
            -> [
                ("first_name", "John"),
                ("first_name", "James")
            ]
            
        arg: first_name
        value: John||first_name=James||company__name=XYZ
            -> [
                ("first_name", "John"),
                ("first_name", "James"),
                ("company__name", "XYZ")
            ]

        Args:
            arg (str): _description_
            value (Any): _description_

        Returns:
            list[tuple[str, Any]]: A list of expressions
        """
        if not isinstance(value, str):
            return [(arg, value)]
        if "||" not in value:
            return [(arg, value)]

        expressions = []
        for part in value.split("||"):
            if "=" in part:
                lookup, expression_value = part.split("=", maxsplit=1)
            else:
                lookup, expression_value = arg, part
            expressions.append((lookup, expression_value))
        return expressions
            
        