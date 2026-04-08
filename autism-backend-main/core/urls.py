from django.urls import path
from .views import (
    RegisterView,
    ChildListCreateView,
    ChildDetailView,
    VoiceUploadView,
    AudioAnalysisListView,
)

urlpatterns = [
    # 1. تسجيل مستخدم جديد (Sign Up)
    path("register/", RegisterView.as_view(), name="register"),

    # 2. إدارة الأطفال (عرض الكل + إضافة طفل جديد)
    path("children/", ChildListCreateView.as_view(), name="children"),
    
    # 3. تفاصيل طفل محدد (عرض بياناته أو حذفه باستخدام الـ ID)
    path("children/<int:pk>/", ChildDetailView.as_view(), name="child-detail"),

    # 4. رفع ملف الصوت للتحليل (هذا اللي يشغل الذكاء الاصطناعي)
    path("upload-voice/", VoiceUploadView.as_view(), name="upload-voice"),
    
    # 5. عرض سجل النتائج والتحليلات السابقة
    path("results/", AudioAnalysisListView.as_view(), name="results"),
]