import os
import joblib
import numpy as np
import librosa
from django.conf import settings

# نفس إعدادات التدريب
N_MFCC = 13
FRAME_SEC = 0.025
HOP_SEC = 0.010
TRIM_SILENCE = True
TOP_DB = 30

# المودلات النهائية
MALE_MODEL = os.path.join(settings.BASE_DIR, "core", "male_final_best_bundle.pkl")
FEMALE_MODEL = os.path.join(settings.BASE_DIR, "core", "female_final_best_bundle.pkl")


def extract_features_v2(y, sr):
    """Extract the same 86 features used in training."""
    if len(y) / sr < 0.05:
        return None

    frame_length = max(256, int(FRAME_SEC * sr))
    hop_length = max(128, int(HOP_SEC * sr))

    mfcc = librosa.feature.mfcc(
        y=y, sr=sr, n_mfcc=N_MFCC,
        n_fft=frame_length, hop_length=hop_length
    )
    d1 = librosa.feature.delta(mfcc, order=1)
    d2 = librosa.feature.delta(mfcc, order=2)

    feats = []
    for arr in (mfcc.T, d1.T, d2.T):
        feats.append(arr.mean(axis=0))
        feats.append(arr.std(axis=0))
    feats = np.concatenate(feats)

    zcr = librosa.feature.zero_crossing_rate(
        y, frame_length=frame_length, hop_length=hop_length
    )[0]
    rms = librosa.feature.rms(
        y=y, frame_length=frame_length, hop_length=hop_length
    )[0]
    centroid = librosa.feature.spectral_centroid(
        y=y, sr=sr, n_fft=frame_length, hop_length=hop_length
    )[0]
    rolloff = librosa.feature.spectral_rolloff(
        y=y, sr=sr, n_fft=frame_length, hop_length=hop_length
    )[0]

    extra = np.array([
        zcr.mean(), zcr.std(),
        rms.mean(), rms.std(),
        centroid.mean(), centroid.std(),
        rolloff.mean(), rolloff.std()
    ])

    x = np.concatenate([feats, extra])
    return np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)


def preprocess_audio(y, sr):
    """Same preprocessing used in final predict script."""
    if TRIM_SILENCE:
        y, _ = librosa.effects.trim(y, top_db=TOP_DB)

    if len(y) == 0:
        raise ValueError("Audio became empty after trimming.")

    m = np.max(np.abs(y))
    if m > 0:
        y = y / (m + 1e-9)

    return y


def load_bundle(gender):
    """Load the correct model bundle based on gender."""
    gender = gender.lower().strip()

    if gender == "male":
        path = MALE_MODEL
    elif gender == "female":
        path = FEMALE_MODEL
    else:
        raise ValueError("gender must be 'male' or 'female'")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Model bundle not found: {path}")

    bundle = joblib.load(path)

    if "model" not in bundle:
        raise ValueError(f"Invalid bundle format in {path}: missing 'model'")

    if "threshold" not in bundle:
        bundle["threshold"] = 0.50

    return bundle


def predict_asd(file_path, gender):
    """Run inference on one audio file and return the result."""
    y, sr = librosa.load(file_path, sr=None)
    y = preprocess_audio(y, sr)

    x = extract_features_v2(y, sr)
    if x is None:
        raise ValueError("Audio too short for feature extraction.")

    x = x.reshape(1, -1)

    bundle = load_bundle(gender)
    model = bundle["model"]
    threshold = float(bundle["threshold"])

    if not hasattr(model, "predict_proba"):
        raise ValueError("Loaded model does not support predict_proba().")

    prob_asd = float(model.predict_proba(x)[0][1])
    prediction = "ASD" if prob_asd >= threshold else "TD"

    return {
        "gender": gender,
        "label": prediction,
        "prob": round(prob_asd, 4),
        "threshold": threshold
    }