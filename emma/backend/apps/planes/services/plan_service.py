"""Write services for action plans."""

from django.db import transaction

from backend.apps.planes.models import PlanAccion


class PlanService:
    @staticmethod
    @transaction.atomic
    def crear_plan(validated_data):
        return PlanAccion.objects.create(**validated_data)

    @staticmethod
    @transaction.atomic
    def actualizar_plan(plan, validated_data):
        for field, value in validated_data.items():
            setattr(plan, field, value)
        plan.save()
        return plan
