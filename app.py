
import re
import csv
import io
import streamlit as st

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

from risk_engine import calculate_risk


# =========================================================
# INITIALIZATION
# =========================================================

st.set_page_config(
    page_title="Trust Juggler",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_database()

PAGES = [
    "Home",
    "Rider Registration",
    "Verification",
    "Risk Assessment",
    "Admin Dashboard",
]

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Home"

if "navigation_target" not in st.session_state:
    st.session_state["navigation_target"] = None

# Apply navigation before creating the radio widget.
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

    #MainMenu {
        visibility: hidden;
    }

    footer {
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


def safe_get_data(function, label):
    try:
        result = function()
        return list(result) if result is not None else []
    except Exception as error:
        st.error(f"Could not load {label}: {error}")
        return []


def save_risk_assessment(rider_id, result):
    """Save a risk assessment and create an alert for HIGH risk."""
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
        "**Important:** This is a heuristic demonstration score, "
        "not a probability of fraud. Indicators are manually selected "
        "and are not automatically detected."
    )

    if saved:
        st.success("Assessment saved to the database.")
        if alert_created:
            st.warning(
                "A HIGH-risk alert was saved. Review it in "
                "Admin Dashboard → Security Alerts."
            )
        else:
            st.caption("No new high-risk alert was created.")


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
                Trust Juggler is a prototype designed to demonstrate how
                delivery platforms can monitor identity-related risk
                throughout a rider's activity, rather than relying only
                on a single initial verification.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    show_metrics(
        [
            ("REGISTERED RIDERS", len(riders)),
            ("VERIFICATION / RISK LOGS", len(logs)),
            ("UNRESOLVED ALERTS", len(unresolved_alerts)),
        ]
    )

    st.markdown("")
    left, right = st.columns(2)

    with left:
        st.markdown(
            """
            <div class="panel">
                <div class="eyebrow">01 · ONBOARDING</div>
                <div class="panel-title">Rider Registration</div>
                <p class="muted">
                    Register a rider in the local database before
                    testing risk assessment workflows.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Open Rider Registration",
            key="home_registration",
            use_container_width=True,
        ):
            st.session_state["navigation_target"] = "Rider Registration"
            st.rerun()

    with right:
        st.markdown(
            """
            <div class="panel">
                <div class="eyebrow">02 · MONITORING</div>
                <div class="panel-title">Risk Assessment</div>
                <p class="muted">
                    Test verification failures, unrecognized devices,
                    unusual locations, and rapid account switching.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Open Risk Assessment",
            key="home_risk",
            use_container_width=True,
        ):
            st.session_state["navigation_target"] = "Risk Assessment"
            st.rerun()

    st.markdown("")
    st.markdown(
        """
        <div class="panel">
            <div class="panel-title">How the prototype works</div>
            <ol>
                <li>Register a rider.</li>
                <li>Enter risk indicators on the Risk Assessment page.</li>
                <li>Save the assessment to SQLite.</li>
                <li>Review logs and security alerts in the Admin Dashboard.</li>
            </ol>
            <p class="muted">
                Face matching, fingerprint scanning, and automatic device
                or location detection are not performed by this workflow.
            </p>
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
        "Create a rider record for the Trust Juggler prototype.",
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
                placeholder="Enter the rider's full name",
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
    section_heading("Registered riders")

    riders = safe_get_data(get_riders, "registered riders")

    if riders:
        display_rows = [
            {
                "Rider ID": get_rider_id(rider),
                "Full Name": get_rider_name(rider),
                "Email": get_rider_email(rider),
            }
            for rider in riders
        ]

        st.dataframe(
            display_rows,
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
        "Explore the planned identity-verification workflow.",
    )

    st.markdown(
        """
        <div class="panel">
            <div class="eyebrow">VERIFICATION WORKFLOW</div>
            <div class="panel-title">
                Verification is not yet biometric matching
            </div>
            <p class="muted">
                This prototype currently records rider information and
                supports risk assessment. It does not yet compare a live
                face or fingerprint against an enrolled biometric template.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    steps = [
        (
            "01",
            "Select rider",
            "Identify the registered rider whose identity needs checking.",
        ),
        (
            "02",
            "Request verification",
            "Ask the rider to complete an approved verification method.",
        ),
        (
            "03",
            "Record outcome",
            "Store the outcome of the verification attempt.",
        ),
        (
            "04",
            "Assess risk",
            "Combine available indicators into a demonstration risk score.",
        ),
        (
            "05",
            "Review alerts",
            "Send high-risk activity to the administrator for review.",
        ),
    ]

    for number, title, description in steps:
        st.markdown(
            f"""
            <div class="panel" style="margin-bottom:12px;">
                <div style="display:flex;gap:18px;align-items:flex-start;">
                    <div style="
                        color:#e7b84f;
                        font-size:1.5rem;
                        font-family:Georgia,serif;
                        font-weight:bold;
                    ">{number}</div>
                    <div>
                        <div class="panel-title">{title}</div>
                        <div class="muted">{description}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("Open Risk Assessment", use_container_width=True):
        st.session_state["navigation_target"] = "Risk Assessment"
        st.rerun()


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
            selected_rider_id = rider_options.get(selected_rider_label, "")
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
                    rider_id=selected_rider_id,
                    result=result,
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
                    "The risk score was calculated, but saving it failed: "
                    f"{error}"
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
        "Review riders, risk assessments, and security alerts.",
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

    show_metrics(
        [
            ("REGISTERED RIDERS", len(riders)),
            ("VERIFICATION / RISK LOGS", len(logs)),
            ("ALL SECURITY ALERTS", len(alerts)),
            ("UNRESOLVED ALERTS", len(unresolved_alerts)),
        ]
    )

    # -----------------------------------------------------
    # REGISTERED RIDERS
    # -----------------------------------------------------

    st.markdown("---")
    section_heading("Registered riders")

    if riders:
        rider_rows = []

        for rider in riders:
            try:
                face_enrolled = bool(rider["face_enrolled"])
            except (KeyError, IndexError):
                face_enrolled = False

            try:
                fingerprint_enrolled = bool(
                    rider["fingerprint_enrolled"]
                )
            except (KeyError, IndexError):
                fingerprint_enrolled = False

            rider_rows.append(
                {
                    "Rider ID": get_rider_id(rider),
                    "Full Name": get_rider_name(rider),
                    "Email": get_rider_email(rider),
                    "Face Enrolled": face_enrolled,
                    "Fingerprint Enrolled": fingerprint_enrolled,
                }
            )

        st.dataframe(
            rider_rows,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No registered riders found.")

    # -----------------------------------------------------
    # VERIFICATION LOGS
    # -----------------------------------------------------

    st.markdown("---")
    section_heading(
        "Verification Logs",
        "Risk assessments are recorded with method = risk_assessment.",
    )

    log_rows = []

    if logs:
        for log in logs:
            try:
                log_rows.append(
                    {
                        "ID": log["id"],
                        "Rider ID": log["rider_id"],
                        "Method": log["method"],
                        "Result": log["result"],
                        "Risk Score": log["risk_score"],
                        "Details": log["details"] or "",
                        "Created At": log["created_at"],
                    }
                )
            except (KeyError, IndexError):
                log_rows.append(dict(log))

        st.dataframe(
            log_rows,
            use_container_width=True,
            hide_index=True,
        )

        risk_log_count = sum(
            1
            for row in log_rows
            if str(row.get("Method", "")).lower() == "risk_assessment"
        )

        st.caption(f"Risk assessments found in logs: {risk_log_count}")
    else:
        st.info("No verification or risk assessment logs found.")

    # -----------------------------------------------------
    # SECURITY ALERTS
    # -----------------------------------------------------

    st.markdown("---")
    section_heading(
        "Security Alerts",
        "Review alerts and mark them resolved without deleting them.",
    )

    alert_rows = []

    if alerts:
        for alert in alerts:
            try:
                resolved = int(alert["resolved"]) == 1
                alert_rows.append(
                    {
                        "ID": alert["id"],
                        "Rider ID": alert["rider_id"],
                        "Alert Type": alert["alert_type"],
                        "Description": alert["description"],
                        "Risk Score": alert["risk_score"],
                        "Resolved": "Yes" if resolved else "No",
                        "Created At": alert["created_at"],
                    }
                )
            except (KeyError, IndexError):
                alert_rows.append(dict(alert))

        st.dataframe(
            alert_rows,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No security alerts found.")

    # -----------------------------------------------------
    # RESOLVE ALERT
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CSV EXPORT
    # -----------------------------------------------------

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
