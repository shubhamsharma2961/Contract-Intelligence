from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'uploaded_at']

class AskSerializer(serializers.Serializer):
    document_id = serializers.IntegerField(required=True, help_text="ID of the document to query.")
    question = serializers.CharField(required=True, help_text="The question to ask about the document.")

class ExtractRequestSerializer(serializers.Serializer):
    pass