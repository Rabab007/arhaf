from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import AudioAnalysis, Child
from .serializers import (
    AudioAnalysisSerializer,
    RegisterSerializer,
    ChildSerializer,
)

# استيراد دالة التنبؤ من ملف الـ ML الخاص بك
try:
    from .ml_inference import predict_asd
except ImportError:
    predict_asd = None

# 1. تسجيل مستخدم جديد
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

# 2. عرض وإضافة الأطفال
class ChildListCreateView(generics.ListCreateAPIView):
    serializer_class = ChildSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Child.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)

# 3. عرض وتعديل بيانات طفل محدد
class ChildDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChildSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Child.objects.filter(parent=self.request.user)

# 4. عرض قائمة التحليلات 
class AudioAnalysisListView(generics.ListAPIView):
    serializer_class = AudioAnalysisSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AudioAnalysis.objects.filter(child__parent=self.request.user)

# 5. رفع وتحليل الصوت (الربط مع موديل الذكاء الاصطناعي)
class VoiceUploadView(APIView):
    authentication_classes = [JWTAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AudioAnalysisSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # حفظ سجل التحليل في قاعدة البيانات أولاً
        analysis = serializer.save()

        # تشغيل موديل الذكاء الاصطناعي الحقيقي
        if predict_asd and analysis.audio_file:
            try:
                # نرسل مسار الملف وجنس الطفل للموديل
                result = predict_asd(analysis.audio_file.path, analysis.child.gender)
                
                # تحديث السجل بالنتائج الحقيقية
                analysis.prediction_result = result["label"]
                # تحويل النسبة لمئوية (مثلاً 0.95 تصير 95.0)
                analysis.confidence_score = round(float(result["prob"]) * 100, 2)
                analysis.save()
            except Exception as e:
                print(f"ML Inference Error: {e}")
                # في حال الخطأ نترك النتيجة "Error" لتعرفي أن هناك مشكلة في الموديل
                analysis.prediction_result = "Analysis Error"
                analysis.save()

        return Response({
            "id": analysis.id,
            "prediction_result": analysis.prediction_result, 
            "confidence_score": analysis.confidence_score,
            "notes": analysis.notes,
            "created_at": analysis.created_at
        }, status=status.HTTP_201_CREATED)
