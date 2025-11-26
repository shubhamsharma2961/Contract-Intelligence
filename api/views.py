import json
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.conf import settings
from .models import Document
from .serializers import DocumentSerializer, AskSerializer
from .utils import extract_text_from_pdf, query_llm

class IngestView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file uploaded. Please use 'file' in multipart/form-data."}, status=400)
        
        doc = Document.objects.create(file=file_obj, title=file_obj.name)
        
        try:
            full_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
            text = extract_text_from_pdf(full_path)
        except Exception as e:
             doc.delete() 
             return Response({"error": f"Failed to process PDF: {str(e)}"}, status=500)

        doc.extracted_text = text
        doc.save()

        return Response({
            "message": "Ingestion successful", 
            "document_id": doc.id,
            "char_count": len(text)
        }, status=201)

class ExtractView(APIView):
    def post(self, request, doc_id):
        try:
            doc = Document.objects.get(id=doc_id)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=404)

        system_prompt = """
        You are a Legal Intelligence AI. Your task is to extract the following 
        fields from the provided contract text and return the result as a single 
        VALID JSON object. If a field is not found, use null or an empty string/array.
        
        Fields to extract:
        - parties (list of names)
        - effective_date (string, e.g., 'YYYY-MM-DD')
        - agreement_term (string, e.g., '3 years' or 'Until terminated')
        - governing_law (string, e.g., 'State of New York')
        - payment_terms (summary of schedule or due dates)
        - termination (summary of notice period and conditions)
        - auto_renewal (boolean or summary of the clause)
        - confidentiality (summary of the clause)
        - indemnity (summary of the clause)
        - liability_cap (string, e.g., '10000 USD' or 'Unlimited')
        - signatories (list of objects: [{"name": "...", "title": "..."}])
        """
        
        text_content = doc.extracted_text[:30000] 
        
        response_text = query_llm(system_prompt, text_content, model="gpt-3.5-turbo-16k") 

        try:
            cleaned_json = response_text.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned_json)
            return Response(data)
        except json.JSONDecodeError:
            return Response({
                "error": "LLM returned invalid JSON",
                "raw_response": response_text
            }, status=500)

class AskView(APIView):
    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc_id = serializer.validated_data['document_id']
        question = serializer.validated_data['question']

        try:
            doc = Document.objects.get(id=doc_id)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=404)

        prompt = f"""
        CONTEXT: {doc.extracted_text[:20000]}
        
        QUESTION: {question}
        
        Answer the question based ONLY on the context provided. 
        If the answer is not in the context, state: "I cannot find a definitive answer in the document."
        """
        
        answer = query_llm(None, prompt, model="gpt-3.5-turbo-16k") 
        
        return Response({
            "question": question,
            "answer": answer,
            "document_id": doc_id,
            "citation": f"Document ID: {doc_id}" 
        })

class AuditView(APIView):
    def post(self, request, doc_id):
        try:
            doc = Document.objects.get(id=doc_id)
        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=404)

        system_prompt = """
        You are a Legal Risk Analyst AI. Review the contract text. Identify all "Risky Clauses" 
        from this list:
        1. Auto-renewal clause with a notice period less than 30 days.
        2. Clauses that enforce "Unlimited Liability" for one party.
        3. Clauses with excessively broad or one-sided indemnity obligations.
        
        Return the findings as a list of JSON objects:
        [
          {"clause_name": "...", "risk_level": "High/Medium/Low", "explanation": "...", "evidence_span": "text excerpt"},
          ...
        ]
        Return ONLY valid JSON.
        """
        
        audit_result = query_llm(system_prompt, doc.extracted_text[:30000], model="gpt-3.5-turbo-16k")
        
        try:
            cleaned_json = audit_result.strip().replace("```json", "").replace("```", "")
            data = json.loads(cleaned_json)
            return Response(data)
        except json.JSONDecodeError:
            return Response({
                "error": "LLM returned invalid JSON for audit report",
                "raw_response": audit_result
            }, status=500)

class HealthCheckView(APIView):
    def get(self, request):
        db_status = 'ok'
        try:
            Document.objects.exists()
        except Exception:
            db_status = 'error'
        
        llm_status = 'ok' if os.environ.get("OPENAI_API_KEY") else 'error'

        return Response({
            "status": "up",
            "db_status": db_status,
            "llm_status": llm_status,
        }, status=200)