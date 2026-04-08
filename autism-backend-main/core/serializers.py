from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Child, AudioAnalysis

# 1. تسجيل المستخدم
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "password", "email")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

# 2. إدارة الأطفال (مع منع العمر السالب 🛡️)
class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = ["id", "name", "age_months", "gender"]

    # 🛡️ تصحيح تلقائي من طرف الباك-إند 
    def validate_age_months(self, value):
        # abs() دالة سحرية تحول أي رقم سالب لموجب (مثلاً -3 تصير 3)
        # كذا لو البنات أرسلوا سالب، الباك-إند حقك بيعدله ويحفظه صح
        return abs(value)

# 3. تحليل الصوت والنتائج
class AudioAnalysisSerializer(serializers.ModelSerializer):
    # حقول للقراءة فقط لأن الموديل والباك إند هم اللي يحسبونها
    prediction_result = serializers.CharField(read_only=True)
    confidence_score = serializers.FloatField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = AudioAnalysis
        fields = [
            "id",
            "child",
            "audio_file",
            "prediction_result",
            "confidence_score",
            "created_at",
            "notes", 
        ]

    def validate_audio_file(self, value):
        # التأكد من أن الملف بصيغة WAV
        if not value.name.lower().endswith(".wav"):
            raise serializers.ValidationError("فقط ملفات الصوت بصيغة .WAV مسموح بها.")
        return value

    def validate_child(self, child):
        # التأكد من ملكية الطفل للمستخدم الحالي (أمان)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            # ملاحظة: تأكدي أن حقل العلاقة في موديل Child اسمه parent
            if child.parent != request.user:
                raise serializers.ValidationError("هذا الطفل غير مسجل تحت حسابك.")
        return child