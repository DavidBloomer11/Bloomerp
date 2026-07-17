from dataclasses import dataclass

from django import forms
    
@dataclass
class Step:
    id: str
    widget: forms.Widget

class MultiStepWidget(forms.Widget):
    steps: list[Step]
    
    pass




multi_step_widget = MultiStepWidget(
    steps=[
        Step(
            id="values",
            widget=forms.MultipleChoiceField()
        )
    ]
)