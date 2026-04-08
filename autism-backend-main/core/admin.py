from django.contrib import admin
from .models import Child, AudioAnalysis
from .ml_inference import predict_asd

@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "age_months", "gender", "parent")
    search_fields = ("name",)
    list_filter = ("gender",)

@admin.register(AudioAnalysis)
class AudioAnalysisAdmin(admin.ModelAdmin):
    # نستخدم 'display_confidence' بدل 'confidence_score' عشان تطلع الـ % في الجدول
    list_display = ("id", "child", "prediction_result", "display_confidence", "notes", "created_at")
    search_fields = ("child__name",)
    list_filter = ("created_at",)
    readonly_fields = ("prediction_result", "confidence_score", "created_at")

    # دالة لعرض النسبة بشكل جميل في الجدول
    def display_confidence(self, obj):
        if obj.confidence_score:
            # إذا كان الرقم أصلاً مئوي (أكبر من 1) نعرضه كما هو، وإلا نضربه في 100
            val = obj.confidence_score if obj.confidence_score > 1.0 else obj.confidence_score * 100
            return f"{round(val, 2)}%"
        return "0%"
    display_confidence.short_description = "Confidence Score"

    def get_fields(self, request, obj=None):
        base_fields = ("child", "audio_file", "notes") 
        if obj is None:
            return base_fields
        return base_fields + ("prediction_result", "confidence_score", "created_at")

    def save_model(self, request, obj, form, change):
        # حفظ الكائن أولاً للحصول على الملف
        super().save_model(request, obj, form, change)

        if obj.audio_file:
            try:
                # نرسل الملف والجنس للموديل
                res = predict_asd(obj.audio_file.path, obj.child.gender)
                
                # هنا التعديل السحري: نضرب النسبة في 100 قبل الحفظ في قاعدة البيانات
                prob_percent = round(float(res["prob"]) * 100, 2)
                
                AudioAnalysis.objects.filter(pk=obj.pk).update(
                    prediction_result=res["label"],
                    confidence_score=prob_percent, # الحفظ كـ 49.21 بدل 0.49
                )
            except Exception as e:
                AudioAnalysis.objects.filter(pk=obj.pk).update(
                    prediction_result="Error",
                    confidence_score=0,
                )
                print("Prediction error:", e)