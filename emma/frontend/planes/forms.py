from django import forms


class PlanFiltroForm(forms.Form):
    q = forms.CharField(required=False, label="Buscar")
    estado = forms.CharField(required=False, label="Estado")

