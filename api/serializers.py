from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'uploaded_at']

class AskSerializer(serializers.Serializer):
    document_id = serializers.IntegerField(required=True, help_text="ID of the document to query.")
    question = serializers.CharField(required=True, help_text="The question to ask about the document.")

class IngestSerializer(serializers.Serializer):
    file = serializers.FileField(help_text="The contract PDF file to upload.", required=True)

class ExtractRequestSerializer(serializers.Serializer):
    pass