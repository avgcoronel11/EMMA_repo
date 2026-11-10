from django import forms


class EventoFiltroForm(forms.Form):
    q = forms.CharField(required=False, label="Buscar")
    estado = forms.CharField(required=False, label="Estado")

