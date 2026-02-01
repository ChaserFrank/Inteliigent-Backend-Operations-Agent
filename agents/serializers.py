from rest_framework import serializers

class AnalyzeEventRequestSerializer(serializers.Serializer):
    error_type = serializers.CharField()
    message = serializers.CharField()
    stack_trace = serializers.CharField(required=False, allow_blank=True)
    context = serializers.DictField(required=False)

class AgentDecisionResponseSerializer(serializers.Serializer):
    category = serializers.CharField()
    severity = serializers.CharField()
    action = serializers.CharField()
    priority = serializers.IntegerField()
    metadata = serializers.DictField()

class DecideActionRequestSerializer(serializers.Serializer):
    category = serializers.CharField()
    severity = serializers.CharField()
    context = serializers.DictField(required=False)

class ExecuteActionRequestSerializer(serializers.Serializer):
    action = serializers.CharField()
    metadata = serializers.DictField(required=False)

class ValidatePayloadRequestSerializer(serializers.Serializer):
    payload = serializers.DictField()

class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
