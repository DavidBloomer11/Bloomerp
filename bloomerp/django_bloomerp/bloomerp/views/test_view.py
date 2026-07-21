from bloomerp.models.base_bloomerp_model import FieldLayout, LayoutItem, LayoutRow
from bloomerp.router import router
from bloomerp.views.base import BaseBloomerpView
from bloomerp.views.mixins.layout_form_mixin import LayoutFormMixin
from bloomerp.views.mixins.layout_mixin import LayoutMixin
from django.views.generic import TemplateView
from django import forms

class RandomForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()



@router.route(
    "test-view"
)
class TestView(LayoutFormMixin, BaseBloomerpView, TemplateView):
    template_name = "mixins/bloomerp_layout_form_mixin.html"
    
    can_change = False
    form_class = RandomForm
    
    layout = FieldLayout(
        rows=[LayoutRow(
            columns=2,
            items=[
                LayoutItem(
                    id="last_name",
                    colspan=1,
                ),
                LayoutItem(
                    id="first_name",
                    colspan=1,
                )
            ]
        )]
    )
    
    
    
    