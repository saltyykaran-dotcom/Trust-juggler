import re
import csv
import io
from pathlib import Path

import numpy as np
import cv2
import streamlit as st

# set_page_config should be the first Streamlit command
st.set_page_config(
    page_title="Trust Juggler",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Authentication & Session Management
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_type"] = None  # "admin" or "rider"
    st.session_state["user_id"] = None

def show_login():
    # Professional centered login page
    # Custom CSS for login container
    login_css = """
    <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            padding: 40px;
            background: var(--panel);
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
        .login-container h2 {
            color: var(--gold);
            text-align: center;
            margin-bottom: 24px;
        }
        .login-container .stButton > button {
            width: 100%;
        }
    </style>
    """
    st.markdown(login_css, unsafe_allow_html=True)
    st.markdown("""
    <div class='login-container'>
        <h2>🔐 Trust Juggler Login</h2>
    </div>
    """, unsafe_allow_html=True)
    login_type = st.radio("Login as", ("Rider", "Admin"))
    if login_type == "Rider":
        rider_id = st.text_input("Rider ID")
        if st.button("Login"):
            from database import get_riders
            riders = get_riders()
            if any(r["rider_id"] == rider_id for r in riders):
                st.session_state["logged_in"] = True
                st.session_state["user_type"] = "rider"
                st.session_state["user_id"] = rider_id
                st.success("Rider logged in")
                st.rerun()
            else:
                st.error("Rider not found")
    else:
        password = st.text_input("Admin password", type="password")
        if st.button("Login"):
            if password == "admin123":
                st.session_state["logged_in"] = True
                st.session_state["user_type"] = "admin"
                st.session_state["user_id"] = "admin"
                st.success("Admin logged in")
                st.rerun()
            else:
                st.error("Invalid admin password")

# Show login page if not authenticated
if not st.session_state.get("logged_in"):
    show_login()
    st.stop()

# Sidebar logout button (visible only when logged in)
st.sidebar.markdown("---")
if st.session_state.get("logged_in"):
    if st.sidebar.button("Logout"):
        for key in ["logged_in", "user_type", "user_id"]:
            st.session_state.pop(key, None)
        st.rerun()

# --------------------------------------------------
# PAGE NAVIGATION (unchanged below)
# --------------------------------------------------

from database import (
    initialize_database,
    add_rider,
    get_riders,
    get_verification_logs,
    get_security_alerts,
    add_verification_log,
    add_security_alert,
    resolve_security_alert,
)

from risk_engine import calculate_risk, compute_score
from face_verification import validate_rider_id

# =========================================================
# INITIALIZATION
# =========================================================

initialize_database()

FACE_DIR = Path(__file__).parent / "face_data"
FACE_DIR.mkdir(parents=True, exist_ok=True)

# LBPH distance threshold: lower distance = closer match.
# Set this to the same value your old face_verification.py used.
VERIFY_THRESHOLD = 80.0

FACE_SIZE = (200, 200)

PAGES = [
    "Home",
    "Rider Registration",
    "Verification",
    "Risk Assessment",
    "Admin Dashboard",
]

# Restrict admin dashboard view to admin users
if st.session_state.get("user_type") != "admin":
    PAGES = [page for page in PAGES if page != "Admin Dashboard"]

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Home"

if "navigation_target" not in st.session_state:
    st.session_state["navigation_target"] = None

target = st.session_state["navigation_target"]

if target in PAGES:
    st.session_state["current_page"] = target

st.session_state["navigation_target"] = None


# =========================================================
# STYLING
# =========================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');

    :root {
        --ink: #261c32;
        --purple: #57276d;
        --plum: #74368a;
        --gold: #e7b84f;
        --cream: #fff9ed;
        --paper: #f6eddc;
        --muted: #a99bb5;
        --panel: #211a2b;
        --panel-light: #30243d;
        --line: rgba(255, 249, 237, 0.12);
    }

    .stApp {
        background:
            radial-gradient(ellipse at top right, #382443 0%, transparent 40%),
            #17131e;
        color: var(--cream);
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(23, 19, 30, 0.85);
    }

    [data-testid="stSidebar"] {
        background: #201829;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] * {
        color: var(--cream);
    }

    [data-testid="stSidebar"] .stRadio label {
        padding: 8px 4px;
    }

    h1, h2, h3 {
        font-family: 'Playfair Display', Georgia, serif !important;
        color: var(--cream) !important;
    }

    p, li, label, .stMarkdown {
        color: var(--cream);
    }

    .brand {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--cream);
        line-height: 1.2;
    }

    .eyebrow {
        color: var(--gold);
        text-transform: uppercase;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 2px;
    }

    .muted {
        color: #b7aabd;
        font-size: 0.94rem;
    }

    .hero {
        background: linear-gradient(135deg, #382443, #211a2b);
        border: 1px solid rgba(231, 184, 79, 0.25);
        border-radius: 20px;
        padding: 32px;
        margin-bottom: 24px;
    }

    .hero-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: clamp(2rem, 4vw, 3.4rem);
        line-height: 1.12;
        color: var(--cream);
        margin: 12px 0;
    }

    .hero-description {
        color: #d6c8dc;
        max-width: 700px;
        line-height: 1.7;
    }

    .panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 22px;
        height: 100%;
    }

    .panel-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.25rem;
        margin-bottom: 8px;
        color: var(--cream);
    }

    .metric-card {
        background: linear-gradient(145deg, #30243d, #211a2b);
        border: 1px solid var(--line);
        border-radius: 15px;
        padding: 18px;
    }

    .metric-label {
        color: #c4b5cc;
        font-size: 0.8rem;
        margin-bottom: 8px;
    }

    .metric-value {
        font-family: 'Playfair Display', Georgia, serif;
        color: var(--gold);
        font-size: 2rem;
        font-weight: 700;
    }

    .risk-result {
        background: #211a2b;
        border: 1px solid rgba(231, 184, 79, 0.35);
        border-radius: 16px;
        padding: 22px;
        margin: 18px 0;
    }

    .risk-score {
        font-family: 'Playfair Display', Georgia, serif;
        color: var(--gold);
        font-size: 3rem;
        font-weight: 700;
    }

    .stButton > button {
        background: var(--gold);
        color: #211829;
        border: 1px solid var(--gold);
        border-radius: 9px;
        font-weight: 700;
        padding: 0.55rem 1rem;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background: #f4d37e;
        border-color: #f4d37e;
        color: #211829;
        transform: translateY(-1px);
    }

    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"],
    .stDateInput input,
    .stTimeInput input {
        background: #30243d !important;
        color: var(--cream) !important;
        border-color: #51405f !important;
        border-radius: 8px !important;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 10px;
        overflow: hidden;
    }

    div[data-testid="stMetric"] {
        background: #30243d;
        border: 1px solid var(--line);
        padding: 15px;
        border-radius: 12px;
    }

    div[data-testid="stMetric"] label {
        color: #c4b5cc !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--gold) !important;
    }

    hr {
        border-color: var(--line);
    }

    .footer {
        border-top: 1px solid var(--line);
        padding-top: 18px;
        margin-top: 40px;
        color: #a99bb5;
        font-size: 0.8rem;
        text-align: center;
    }

    #MainMenu, footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def page_heading(title, subtitle):
    st.markdown(
        f"""
        <div style="margin-bottom:24px;">
            <div class="eyebrow">THE TRUST JUGGLER · ICT MUMBAI</div>
            <h1 style="margin:8px 0;">{title}</h1>
            <div class="muted">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title, subtitle=None):
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def show_metrics(items):
    columns = st.columns(len(items))
    for column, (label, value) in zip(columns, items):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def get_rider_id(rider):
    try:
        return str(rider["rider_id"])
    except (KeyError, TypeError, IndexError):
        return ""


def get_rider_name(rider):
    try:
        return str(rider["full_name"])
    except (KeyError, TypeError, IndexError):
        return "Unknown rider"


def get_rider_email(rider):
    try:
        return str(rider["email"])
    except (KeyError, TypeError, IndexError):
        return ""


def has_enrolled_face(rider_id):
    if not validate_rider_id(rider_id):
        return False
    return (FACE_DIR / f"{rider_id}.jpg").is_file()


def safe_get_data(function, label):
    try:
        result = function()
        return list(result) if result is not None else []
    except Exception as error:
        st.error(f"Could not load {label}: {error}")
        return []


# ---------------------------------------------------------
# Browser-camera face helpers (replace the OpenCV window)
# ---------------------------------------------------------

def _decode_image(image_bytes):
    """Decode raw image bytes (from st.camera_input) to a BGR array."""
    array = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(array, cv2.IMREAD_COLOR)


_CASCADE_CACHE = []
_CASCADE_DEBUG = []


def _cascade_search_dirs():
    dirs = []
    try:
        dirs.append(Path(cv2.data.haarcascades))
    except AttributeError:
        pass
    cv2_dir = Path(cv2.__file__).parent
    dirs.append(cv2_dir / "data")
    dirs.append(cv2_dir.parent / "cv2" / "data")
    dirs.append(Path(__file__).parent / "models")
    return [d for d in dirs if d.is_dir()]


def _load_cascades():
    """Load Haar face models. Retries via a safe ASCII path if needed."""
    if _CASCADE_CACHE:
        return _CASCADE_CACHE

    safe_dirs = [
        Path(__file__).parent / "models_cache",
        Path.home() / ".trust_juggler_models",
        Path("C:/tj_models") if Path("C:/").exists() else Path("/tmp/tj_models"),
    ]

    for name in (
        "haarcascade_frontalface_default.xml",
        "haarcascade_frontalface_alt2.xml",
        "haarcascade_frontalface_alt.xml",
    ):
        source = None
        for directory in _cascade_search_dirs():
            if (directory / name).is_file():
                source = directory / name
                break
        if source is None:
            continue

        cascade = cv2.CascadeClassifier(str(source))

        # OpenCV often cannot open files under non-ASCII paths
        # (e.g. a Windows username with special characters).
        if cascade.empty():
            for safe in safe_dirs:
                try:
                    safe.mkdir(parents=True, exist_ok=True)
                    target = safe / name
                    target.write_bytes(source.read_bytes())
                    cascade = cv2.CascadeClassifier(str(target))
                    if not cascade.empty():
                        break
                except Exception:
                    continue

        if not cascade.empty():
            _CASCADE_CACHE.append(cascade)

    # Last resort: download the model file from the OpenCV repository.
    if not _CASCADE_CACHE:
        import socket
        import urllib.request

        socket.setdefaulttimeout(5)

        name = "haarcascade_frontalface_default.xml"
        url = (
            "https://raw.githubusercontent.com/opencv/opencv/4.x/"
            "data/haarcascades/" + name
        )
        targets = [Path(__file__).parent / "models"] + safe_dirs
        for directory in targets:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                target = directory / name
                if not target.is_file() or target.stat().st_size < 1000:
                    urllib.request.urlretrieve(url, str(target))
                cascade = cv2.CascadeClassifier(str(target))
                if not cascade.empty():
                    _CASCADE_CACHE.append(cascade)
                    break
                _CASCADE_DEBUG.append(f"Loaded file but empty: {target}")
            except Exception as error:
                _CASCADE_DEBUG.append(f"{directory}: {error}")

    return _CASCADE_CACHE


def _cascade_debug_text():
    try:
        data_dir = cv2.data.haarcascades
    except AttributeError:
        data_dir = "cv2.data not available"
    searched = ", ".join(str(d) for d in _cascade_search_dirs()) or "none"
    return (
        f"OpenCV {cv2.__version__}; data dir: {data_dir}; "
        f"searched: {searched}; "
        f"details: {' | '.join(_CASCADE_DEBUG) or 'none'}"
    )


def _extract_face(gray):
    """Return a cropped, resized grayscale face, or None if not exactly one."""
    cascades = _load_cascades()
    if not cascades:
        return None

    # Try raw, histogram-equalised and CLAHE versions of the image,
    # since lighting is the most common reason detection fails.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    variants = [gray, cv2.equalizeHist(gray), clahe.apply(gray)]

    for variant in variants:
        for cascade in cascades:
            for scale, neighbors, min_size in (
                (1.1, 5, (60, 60)),
                (1.05, 4, (50, 50)),
                (1.05, 3, (40, 40)),
            ):
                faces = cascade.detectMultiScale(
                    variant,
                    scaleFactor=scale,
                    minNeighbors=neighbors,
                    minSize=min_size,
                )
                if len(faces) > 0:
                    # Use the largest face if several are detected.
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    return cv2.resize(
                        variant[y:y + h, x:x + w], FACE_SIZE
                    )

    return None


def _face_or_fallback(gray):
    """Return (face, detector_used).

    If the face models load, detection is required (None if no face).
    If they cannot be loaded at all, fall back to a centred square crop
    so the prototype keeps working; the caller shows a warning.
    """
    if _load_cascades():
        return _extract_face(gray), True

    height, width = gray.shape[:2]
    side = int(min(height, width) * 0.7)
    top = (height - side) // 2
    left = (width - side) // 2
    crop = gray[top:top + side, left:left + side]
    crop = cv2.equalizeHist(crop)
    return cv2.resize(crop, FACE_SIZE), False


def enroll_face_from_bytes(rider_id, image_bytes):
    """Validate a captured photo and save the face image for this rider."""
    if not validate_rider_id(rider_id):
        return {"success": False, "message": "Invalid rider ID."}

    image = _decode_image(image_bytes)
    if image is None:
        return {"success": False, "message": "Could not read the photo."}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face, detected = _face_or_fallback(gray)
    if face is None:
        return {
            "success": False,
            "message": (
                "No face was detected in the photo. Face the camera "
                "directly, keep your whole face in frame, remove glasses "
                "or a cap if possible, and make sure light falls on your "
                "face rather than behind you."
            ),
        }

    path = FACE_DIR / f"{rider_id}.jpg"
    if not cv2.imwrite(str(path), face):
        return {"success": False, "message": "Could not save the face image."}

    message = f"Face enrolled for rider {rider_id}."
    if not detected:
        message += (
            " Note: the face detector could not be loaded, so the centre "
            "of the photo was saved without checking for a face. Keep the "
            "face centred when verifying."
        )
    return {"success": True, "message": message}


def verify_face_from_bytes(rider_id, image_bytes):
    """Compare a captured photo with the enrolled face using LBPH."""
    if not hasattr(cv2, "face"):
        return {
            "success": False,
            "message": (
                "OpenCV face module missing. Install it with: "
                "pip install opencv-contrib-python"
            ),
        }

    if not validate_rider_id(rider_id) or not has_enrolled_face(rider_id):
        return {"success": False, "message": "No enrolled face for this rider."}

    stored = cv2.imread(str(FACE_DIR / f"{rider_id}.jpg"), cv2.IMREAD_GRAYSCALE)
    if stored is None:
        return {"success": False, "message": "Could not read the enrolled image."}
    # Older enrollments may be full frames; crop if a face is found.
    stored_face = _extract_face(stored)
    if stored_face is None:
        stored_face = cv2.resize(stored, FACE_SIZE)

    image = _decode_image(image_bytes)
    if image is None:
        return {"success": False, "message": "Could not read the photo."}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    live_face, _ = _face_or_fallback(gray)
    if live_face is None:
        return {
            "success": False,
            "message": (
                "No face was detected in the photo. Face the camera "
                "directly, keep your whole face in frame, and make sure "
                "light falls on your face."
            ),
        }

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train([stored_face], np.array([0]))
    _, distance = recognizer.predict(live_face)

    verified = distance <= VERIFY_THRESHOLD
    return {
        "success": True,
        "verified": verified,
        "distance": float(distance),
        "message": (
            "Face is similar to the enrolled image."
            if verified
            else "Face is not similar enough to the enrolled image."
        ),
    }


def save_risk_assessment(rider_id, result):
    details = "; ".join(result["reasons"])
    details = (
        f"Risk assessment. Indicators: {details}. "
        f"Recommended action: {result['recommended_action']}"
    )

    add_verification_log(
        rider_id=rider_id,
        method="risk_assessment",
        result="assessed",
        risk_score=result["score"],
        details=details,
    )

    alert_created = False

    if result["level"] == "HIGH":
        add_security_alert(
            rider_id=rider_id,
            alert_type="high_risk_activity",
            description=(
                f"High-risk assessment: {result['score']}/100. "
                f"Indicators: {'; '.join(result['reasons'])}"
            ),
            risk_score=result["score"],
        )
        alert_created = True

    return alert_created


def show_risk_result(rider_id, result, saved=False, alert_created=False):
    st.markdown("---")
    section_heading("Assessment result", f"Rider ID: {rider_id}")

    st.markdown(
        f"""
        <div class="risk-result">
            <div class="eyebrow">CALCULATED RISK SCORE</div>
            <div class="risk-score">{result['score']}<span
                style="font-size:1.2rem;color:#c4b5cc;"> / 100</span></div>
            <div style="font-size:1.1rem;font-weight:700;">
                Risk level: {result['level']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if result["level"] == "HIGH":
        st.error("HIGH RISK — " + result["recommended_action"])
    elif result["level"] == "MEDIUM":
        st.warning("MEDIUM RISK — " + result["recommended_action"])
    else:
        st.success("LOW RISK — " + result["recommended_action"])

    st.markdown("**Risk indicators**")
    for reason in result["reasons"]:
        st.markdown(f"- {reason}")

    st.info(
        "This is a heuristic demonstration score, not a probability "
        "of fraud. Results depend on the selected indicators."
    )

    if saved:
        st.success("Assessment saved to the database.")
        if alert_created:
            st.warning(
                "A HIGH-risk alert was saved. Review it in "
                "Admin Dashboard → Security Alerts."
            )


def log_face_verification(rider_id, result):
    """Save a face-verification attempt using the existing log API."""

    if not result.get("success"):
        log_result = "error"
        details = result.get("message", "Verification could not be completed.")
    elif result.get("verified"):
        log_result = "success"
        details = (
            f"{result.get('message', 'Possible face match.')}"
            f" Matching distance: {result.get('distance', 'N/A')}"
        )
    else:
        log_result = "failed"
        details = (
            f"{result.get('message', 'Face did not match.')}"
            f" Matching distance: {result.get('distance', 'N/A')}"
        )

    add_verification_log(
        rider_id=rider_id,
        method="face_verification",
        result=log_result,
        risk_score=0,
        details=details,
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown(
        """
        <div style="padding:10px 0 22px 0;">
            <div style="font-size:2rem;">🛡️</div>
            <div class="brand">Trust Juggler</div>
            <div class="eyebrow" style="margin-top:8px;">
                Security Console
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption("WORKSPACE")

    page = st.radio(
        "WORKSPACE",
        PAGES,
        key="current_page",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("CONTINUOUS IDENTITY VERIFICATION")
    st.caption("Prototype · Local SQLite database")


# =========================================================
# HOME PAGE
# =========================================================

if page == "Home":
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">CONTINUOUS IDENTITY VERIFICATION</div>
            <div class="hero-title">Trust is not a one-time check.</div>
            <div class="hero-description">
                Trust Juggler demonstrates how delivery platforms can
                monitor identity-related risk during rider activity.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    riders = safe_get_data(get_riders, "registered riders")
    logs = safe_get_data(get_verification_logs, "verification logs")
    alerts = safe_get_data(get_security_alerts, "security alerts")

    unresolved_alerts = [
        alert for alert in alerts
        if str(alert["resolved"] if "resolved" in alert.keys() else 0) == "0"
    ]

    show_metrics([
        ("REGISTERED RIDERS", len(riders)),
        ("VERIFICATION / RISK LOGS", len(logs)),
        ("UNRESOLVED ALERTS", len(unresolved_alerts)),
    ])

    # Display continuous behavioral score for each rider
    if riders:
        score_rows = []
        for rider in riders:
            rider_id = get_rider_id(rider)
            score_info = compute_score(rider_id)
            score_rows.append({
                "Rider ID": rider_id,
                "Base Score": score_info.get("base_score"),
                "Hand‑off Penalty": score_info.get("hand_off"),
                "Total Score": score_info.get("total"),
                "Level": score_info.get("level"),
            })
        st.subheader("Behavioral Scores")
        st.dataframe(score_rows, use_container_width=True, hide_index=True)

    st.markdown("")
    left, right = st.columns(2)

    with left:
        st.markdown(
            """
            <div class="panel">
                <div class="eyebrow">01 · ONBOARDING</div>
                <div class="panel-title">Rider Registration</div>
                <p class="muted">
                    Register riders and enroll their faces with consent.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Rider Registration",
                     key="home_registration",
                     use_container_width=True):
            st.session_state["navigation_target"] = "Rider Registration"
            st.rerun()

    with right:
        st.markdown(
            """
            <div class="panel">
                <div class="eyebrow">02 · BIOMETRIC CHECK</div>
                <div class="panel-title">Face Verification</div>
                <p class="muted">
                    Compare a live camera photo with an enrolled face image.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Verification",
                     key="home_verification",
                     use_container_width=True):
            st.session_state["navigation_target"] = "Verification"
            st.rerun()

    st.markdown("")
    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">How the prototype works</div>
            <ol>
                <li>Register a rider.</li>
                <li>Obtain consent and enroll a face image.</li>
                <li>Compare a live face during verification.</li>
                <li>Log the outcome and assess failed attempts.</li>
                <li>Review risk assessments and alerts.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# RIDER REGISTRATION PAGE
# =========================================================

elif page == "Rider Registration":
    page_heading(
        "Rider Registration",
        "Create a rider record before enrolling a face.",
    )

    with st.form("rider_registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            rider_id = st.text_input(
                "Rider ID",
                placeholder="e.g. RIDER001",
            )
            full_name = st.text_input(
                "Full Name",
                placeholder="Enter full name",
            )

        with col2:
            email = st.text_input(
                "Email Address",
                placeholder="rider@example.com",
            )

        submitted = st.form_submit_button(
            "Register Rider",
            use_container_width=True,
        )

        if submitted:
            rider_id = rider_id.strip()
            full_name = full_name.strip()
            email = email.strip().lower()

            if not rider_id or not full_name or not email:
                st.error("Please fill in all three fields.")
            elif not validate_rider_id(rider_id):
                st.error(
                    "Rider ID can contain only letters, numbers, "
                    "underscores and hyphens."
                )
            elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                st.error("Please enter a valid email address.")
            else:
                try:
                    add_rider(
                        rider_id=rider_id,
                        full_name=full_name,
                        email=email,
                    )
                    st.success(
                        f"Rider {rider_id} registered successfully."
                    )
                except Exception as error:
                    error_text = str(error).lower()
                    if "unique" in error_text or "duplicate" in error_text:
                        st.error(
                            "That Rider ID or email is already registered."
                        )
                    else:
                        st.error(f"Could not register rider: {error}")

    st.markdown("---")
    section_heading(
        "Face enrollment",
        "Obtain the rider's consent before saving a face image.",
    )

    riders = safe_get_data(get_riders, "registered riders")

    rider_options = {
        f"{get_rider_id(rider)} — {get_rider_name(rider)}":
        get_rider_id(rider)
        for rider in riders
        if get_rider_id(rider)
    }

    if not rider_options:
        st.info("Register a rider before enrolling a face.")
    else:
        selected_label = st.selectbox(
            "Select rider for enrollment",
            options=list(rider_options.keys()),
            key="enroll_rider",
        )
        selected_id = rider_options[selected_label]

        flash = st.session_state.pop("enroll_flash", None)
        if flash:
            st.success(flash)

        if has_enrolled_face(selected_id):
            st.success("A face image is already enrolled for this rider.")
            st.caption(
                "Enrolling again replaces the existing image for this ID."
            )
        else:
            st.info("No face image is currently enrolled for this rider.")

        consent = st.checkbox(
            "The rider has given informed consent to capture and store "
            "their face image.",
            key="face_enrollment_consent",
        )

        if "enroll_cam_n" not in st.session_state:
            st.session_state["enroll_cam_n"] = 0

        photo = None
        if consent:
            st.caption(
                "Allow camera access in your browser when prompted, "
                "face the camera in good light, then take the photo."
            )
            photo = st.camera_input(
                "Take a photo to enroll",
                key=f"enroll_cam_{selected_id}_"
                    f"{st.session_state['enroll_cam_n']}",
            )

        if st.button(
            "Enroll Captured Face",
            disabled=not (consent and photo is not None),
            use_container_width=True,
        ):
            with st.spinner("Processing photo..."):
                enrollment = enroll_face_from_bytes(
                    selected_id, photo.getvalue()
                )

            if enrollment.get("success"):
                try:
                    add_verification_log(
                        rider_id=selected_id,
                        method="face_enrollment",
                        result="success",
                        risk_score=0,
                        details="Face image enrolled with consent.",
                    )
                except Exception as error:
                    st.warning(
                        f"Image saved, but enrollment logging failed: {error}"
                    )
                st.session_state["enroll_flash"] = enrollment["message"]
                st.session_state["enroll_cam_n"] += 1
                st.rerun()
            else:
                st.error(enrollment.get("message", "Enrollment failed."))

    st.markdown("---")
    section_heading("Registered riders")

    riders = safe_get_data(get_riders, "registered riders")

    if riders:
        st.dataframe(
            [
                {
                    "Rider ID": get_rider_id(rider),
                    "Full Name": get_rider_name(rider),
                    "Email": get_rider_email(rider),
                    "Face Enrolled": has_enrolled_face(
                        get_rider_id(rider)
                    ),
                }
                for rider in riders
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No riders have been registered yet.")


# =========================================================
# VERIFICATION PAGE
# =========================================================

elif page == "Verification":
    page_heading(
        "Identity Verification",
        "Compare a live camera photo with the enrolled face image.",
    )

    riders = safe_get_data(get_riders, "registered riders")

    rider_options = {
        f"{get_rider_id(rider)} — {get_rider_name(rider)}":
        get_rider_id(rider)
        for rider in riders
        if get_rider_id(rider)
    }

    if not rider_options:
        st.warning("Register a rider before attempting verification.")
    else:
        selected_label = st.selectbox(
            "Select rider to verify",
            options=list(rider_options.keys()),
            key="verify_rider",
        )
        selected_id = rider_options[selected_label]

        if has_enrolled_face(selected_id):
            st.success("An enrolled face image was found.")
        else:
            st.warning(
                "This rider has no enrolled face image. "
                "Go to Rider Registration and enroll a face first."
            )

        st.markdown(
            """
            <div class="panel">
                <div class="panel-title">Before you begin</div>
                <p class="muted">
                    Obtain the rider's consent for this verification attempt.
                    Your browser will ask for camera access. Take a photo
                    facing the camera, then press Start Face Verification.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        verification_consent = st.checkbox(
            "The rider consents to this face-verification attempt.",
            key="face_verification_consent",
        )

        verify_photo = None
        if verification_consent and has_enrolled_face(selected_id):
            verify_photo = st.camera_input(
                "Take a photo to verify",
                key=f"verify_cam_{selected_id}",
            )

        if st.button(
            "Start Face Verification",
            disabled=(
                not verification_consent
                or not has_enrolled_face(selected_id)
                or verify_photo is None
            ),
            use_container_width=True,
        ):
            with st.spinner("Comparing faces..."):
                result = verify_face_from_bytes(
                    selected_id, verify_photo.getvalue()
                )

            st.session_state["last_face_verification"] = {
                "rider_id": selected_id,
                "result": result,
            }

            try:
                log_face_verification(selected_id, result)
            except Exception as error:
                st.error(f"Could not save the verification log: {error}")

            # A completed, unsuccessful comparison is a failed attempt.
            # A camera or detection error is not counted as a mismatch.
            if result.get("success") and not result.get("verified"):
                try:
                    risk_result = calculate_risk(
                        failed_verifications=1,
                        unusual_device=False,
                        unusual_location=False,
                        rapid_account_switching=False,
                    )

                    alert_created = save_risk_assessment(
                        selected_id,
                        risk_result,
                    )

                    st.session_state["last_face_risk"] = {
                        "rider_id": selected_id,
                        "result": risk_result,
                        "saved": True,
                        "alert_created": alert_created,
                    }
                except Exception as error:
                    st.session_state["last_face_risk"] = None
                    st.error(
                        f"The mismatch was logged, but risk assessment "
                        f"saving failed: {error}"
                    )
            else:
                st.session_state["last_face_risk"] = None

        last_face = st.session_state.get("last_face_verification")

        if last_face:
            face_result = last_face["result"]
            st.markdown("---")
            section_heading(
                "Verification result",
                f"Rider ID: {last_face['rider_id']}",
            )

            if not face_result.get("success"):
                st.error(face_result.get("message", "Verification failed."))
            elif face_result.get("verified"):
                st.success("Possible face match detected.")
                st.write(face_result.get("message", ""))
            else:
                st.error("Face did not meet the matching threshold.")
                st.write(face_result.get("message", ""))

            if face_result.get("distance") is not None:
                st.metric(
                    "LBPH matching distance",
                    f"{face_result['distance']:.2f}",
                )
                st.caption(
                    "Lower distances indicate closer image similarity. "
                    "This value is not an accuracy percentage."
                )

            last_risk = st.session_state.get("last_face_risk")
            if last_risk:
                show_risk_result(
                    rider_id=last_risk["rider_id"],
                    result=last_risk["result"],
                    saved=last_risk["saved"],
                    alert_created=last_risk["alert_created"],
                )

    st.markdown("---")
    st.warning(
        "Prototype limitation: LBPH compares image patterns and does not "
        "provide liveness detection. A photograph or replay may fool it. "
        "A possible match is not proof of identity."
    )


# =========================================================
# RISK ASSESSMENT PAGE
# =========================================================

elif page == "Risk Assessment":
    page_heading(
        "Risk Assessment",
        "Calculate a demonstration risk score and save it to the database.",
    )

    riders = safe_get_data(get_riders, "registered riders")

    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">Assessment inputs</div>
            <p class="muted">
                Select a registered rider and choose indicators to simulate.
                This is a rule-based demonstration, not a prediction of fraud.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rider_options = {
        f"{get_rider_id(rider)} — {get_rider_name(rider)}":
        get_rider_id(rider)
        for rider in riders
        if get_rider_id(rider)
    }

    with st.form("risk_assessment_form"):
        if rider_options:
            selected_rider_label = st.selectbox(
                "Select rider",
                options=list(rider_options.keys()),
            )
            manual_rider_id = None
        else:
            st.warning(
                "No registered riders were found. Enter a Rider ID manually "
                "or register a rider first."
            )
            manual_rider_id = st.text_input(
                "Rider ID",
                placeholder="e.g. RIDER001",
            )
            selected_rider_label = None

        st.markdown("#### Risk indicators")

        failed_verifications = st.number_input(
            "Failed verification attempts",
            min_value=0,
            max_value=20,
            value=0,
            step=1,
        )

        col1, col2 = st.columns(2)

        with col1:
            unusual_device = st.checkbox(
                "Unrecognized device detected",
                value=False,
            )
            unusual_location = st.checkbox(
                "Unusual login location detected",
                value=False,
            )

        with col2:
            rapid_account_switching = st.checkbox(
                "Rapid account switching detected",
                value=False,
            )

        submitted = st.form_submit_button(
            "Calculate and Save Risk",
            use_container_width=True,
        )

    if submitted:
        if rider_options:
            selected_rider_id = rider_options.get(
                selected_rider_label, ""
            )
        else:
            selected_rider_id = (manual_rider_id or "").strip()

        if not selected_rider_id:
            st.error("Enter or select a valid Rider ID.")
        else:
            result = calculate_risk(
                failed_verifications=int(failed_verifications),
                unusual_device=unusual_device,
                unusual_location=unusual_location,
                rapid_account_switching=rapid_account_switching,
            )

            try:
                alert_created = save_risk_assessment(
                    selected_rider_id,
                    result,
                )

                st.session_state["last_risk_assessment"] = {
                    "rider_id": selected_rider_id,
                    "result": result,
                    "saved": True,
                    "alert_created": alert_created,
                }
            except Exception as error:
                st.session_state["last_risk_assessment"] = {
                    "rider_id": selected_rider_id,
                    "result": result,
                    "saved": False,
                    "alert_created": False,
                }
                st.error(
                    f"The score was calculated, but saving failed: {error}"
                )

    last_assessment = st.session_state.get("last_risk_assessment")

    if last_assessment:
        show_risk_result(
            rider_id=last_assessment["rider_id"],
            result=last_assessment["result"],
            saved=last_assessment["saved"],
            alert_created=last_assessment["alert_created"],
        )

    st.markdown("---")
    st.caption(
        "Failed attempts contribute up to 35 points, unrecognized device "
        "20, unusual location 25, and rapid account switching 30. "
        "The total is capped at 100."
    )


# =========================================================
# ADMIN DASHBOARD PAGE
# =========================================================

elif page == "Admin Dashboard":
    page_heading(
        "Admin Dashboard",
        "Review riders, biometric attempts, risk assessments, and alerts.",
    )

    if st.button("Refresh Dashboard"):
        st.rerun()

    riders = safe_get_data(get_riders, "registered riders")
    logs = safe_get_data(get_verification_logs, "verification logs")
    alerts = safe_get_data(get_security_alerts, "security alerts")

    unresolved_alerts = []
    for alert in alerts:
        try:
            if int(alert["resolved"]) == 0:
                unresolved_alerts.append(alert)
        except (KeyError, TypeError, ValueError, IndexError):
            unresolved_alerts.append(alert)

    show_metrics([
        ("REGISTERED RIDERS", len(riders)),
        ("VERIFICATION / RISK LOGS", len(logs)),
        ("ALL SECURITY ALERTS", len(alerts)),
        ("UNRESOLVED ALERTS", len(unresolved_alerts)),
    ])

    # REGISTERED RIDERS
    st.markdown("---")
    section_heading("Registered riders")

    if riders:
        # Rider details table
        st.dataframe(
            [
                {
                    "Rider ID": get_rider_id(rider),
                    "Full Name": get_rider_name(rider),
                    "Email": get_rider_email(rider),
                    "Face Enrolled": has_enrolled_face(get_rider_id(rider)),
                }
                for rider in riders
            ],
            use_container_width=True,
            hide_index=True,
        )
        # Behavioral scores table
        score_rows = []
        for rider in riders:
            rider_id = get_rider_id(rider)
            score = compute_score(rider_id)
            score_rows.append({
                "Rider ID": rider_id,
                "Base Score": score.get("base_score"),
                "Hand‑off Penalty": score.get("hand_off"),
                "Total Score": score.get("total"),
                "Level": score.get("level"),
            })
        st.subheader("Behavioral Scores")
        st.dataframe(score_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No registered riders found.")

    # VERIFICATION LOGS
    st.markdown("---")
    section_heading(
        "Verification Logs",
        "Includes face enrollment, face verification, and risk assessments.",
    )

    log_rows = []

    for log in logs:
        try:
            log_rows.append({
                "ID": log["id"],
                "Rider ID": log["rider_id"],
                "Method": log["method"],
                "Result": log["result"],
                "Risk Score": log["risk_score"],
                "Details": log["details"] or "",
                "Created At": log["created_at"],
            })
        except (KeyError, IndexError, TypeError):
            log_rows.append(dict(log))

    if log_rows:
        st.dataframe(
            log_rows,
            use_container_width=True,
            hide_index=True,
        )

        face_log_count = sum(
            1 for row in log_rows
            if str(row.get("Method", "")).startswith("face_")
        )
        risk_log_count = sum(
            1 for row in log_rows
            if str(row.get("Method", "")).lower() == "risk_assessment"
        )

        col1, col2 = st.columns(2)
        col1.metric("Face-related log entries", face_log_count)
        col2.metric("Risk assessments", risk_log_count)
    else:
        st.info("No verification or risk assessment logs found.")

    # SECURITY ALERTS
    st.markdown("---")
    section_heading(
        "Security Alerts",
        "Review alerts and mark them resolved without deleting them.",
    )

    alert_rows = []

    for alert in alerts:
        try:
            resolved = int(alert["resolved"]) == 1
            alert_rows.append({
                "ID": alert["id"],
                "Rider ID": alert["rider_id"],
                "Alert Type": alert["alert_type"],
                "Description": alert["description"],
                "Risk Score": alert["risk_score"],
                "Resolved": "Yes" if resolved else "No",
                "Created At": alert["created_at"],
            })
        except (KeyError, IndexError, TypeError):
            alert_rows.append(dict(alert))

    if alert_rows:
        st.dataframe(
            alert_rows,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No security alerts found.")

    # RESOLVE ALERT
    st.markdown("---")
    section_heading(
        "Resolve an alert",
        "Resolved alerts remain in the database for audit purposes.",
    )

    if unresolved_alerts:
        alert_options = {}

        for alert in unresolved_alerts:
            try:
                alert_id = int(alert["id"])
                rider_id = str(alert["rider_id"])
                alert_type = str(alert["alert_type"])
                risk_score = int(alert["risk_score"])

                label = (
                    f"Alert #{alert_id} — {rider_id} — "
                    f"{alert_type} (Risk: {risk_score})"
                )
                alert_options[label] = alert_id
            except (KeyError, TypeError, ValueError, IndexError):
                continue

        if alert_options:
            selected_alert_label = st.selectbox(
                "Select an unresolved alert",
                options=list(alert_options.keys()),
                key="resolve_alert_select",
            )

            confirm_resolution = st.checkbox(
                "I confirm that I have reviewed this alert.",
                key="confirm_alert_resolution",
            )

            if st.button(
                "Resolve Selected Alert",
                disabled=not confirm_resolution,
                use_container_width=True,
            ):
                selected_alert_id = alert_options[selected_alert_label]

                try:
                    resolve_security_alert(selected_alert_id)
                    st.success(
                        f"Alert #{selected_alert_id} marked as resolved."
                    )
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not resolve alert: {error}")
        else:
            st.warning(
                "Unresolved alerts exist, but their IDs could not be read."
            )
    else:
        st.success("There are no unresolved alerts.")

    # CSV EXPORT
    st.markdown("---")
    section_heading("Export verification logs")

    if log_rows:
        output = io.StringIO()
        fieldnames = list(log_rows[0].keys())

        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(log_rows)

        st.download_button(
            "Download Verification Logs CSV",
            data=output.getvalue(),
            file_name="trust_juggler_verification_logs.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.caption("There are no logs to export yet.")


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        THE TRUST JUGGLER · ICT MUMBAI<br>
        Continuous Identity Verification · Prototype
    </div>
    """,
    unsafe_allow_html=True,
)