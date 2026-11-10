from django import forms


class CatalogoFiltroForm(forms.Form):
    q = forms.CharField(required=False, label="Buscar")

