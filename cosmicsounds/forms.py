from django import forms


class ThresholdForm(forms.Form):
    threshold = forms.IntegerField(
        min_value=0,
        max_value=255,
        initial=80,
        label="Star brightness threshold",
        help_text="Pixels brighter than this (0–255) count as stars. Lower values find more stars.",
        widget=forms.NumberInput(attrs={"type": "range", "step": 5}),
    )
