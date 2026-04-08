from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# 1. موديل بيانات الطفل (Child Model)
class Child(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    # ربط الطفل بالمستخدم (الأب/الأم)
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')
    
    # اسم الطفل
    name = models.CharField(max_length=100)
    
    # 🛡️ قفل العمر: يمنع السالب برمجياً وفي قاعدة البيانات
    age_months = models.IntegerField(
        validators=[
            MinValueValidator(0, message="العمر لا يمكن أن يكون بالسالب!"), 
            MaxValueValidator(60, message="عمر الطفل كبير جداً على هذا الفحص")
        ]
    )
    
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.gender})"

    # 🛠️ تصحيح تلقائي قبل الحفظ: لو البنات أرسلوا سالب من الفرونت، الباك يحوله لموجب صامت
    def save(self, *args, **kwargs):
        if self.age_months < 0:
            self.age_months = abs(self.age_months)
        super().save(*args, **kwargs)


# 2. موديل تحليل الصوت (Audio Analysis Model)
class AudioAnalysis(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='analyses')
    audio_file = models.FileField(upload_to='recordings/')
    prediction_result = models.CharField(max_length=50, blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.child.name} - Result: {self.prediction_result}"

    def save(self, *args, **kwargs):
        # 🎯 تحويل النسبة المئوية تلقائياً (مثلاً 0.85 تصير 85.0)
        if self.confidence_score is not None and self.confidence_score <= 1.0:
             self.confidence_score = round(self.confidence_score * 100, 2)
        super().save(*args, **kwargs)