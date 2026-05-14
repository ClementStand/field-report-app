"""
Field Report - ESADE Assignment
Mobile-friendly Streamlit app: captures researcher info, GPS, photo,
and generates a downloadable PDF report.
"""
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
from PIL import Image
from datetime import datetime
import tempfile
import os

st.set_page_config(page_title="Field Report", page_icon="🗺️", layout="centered")

# ----------------------------- Helpers -----------------------------
def safe(text: str) -> str:
    """Make text safe for the default FPDF font (Latin-1 charset).
    Replaces any character outside Latin-1 with '?'. Handles é, ñ, ü, à, etc."""
    if text is None:
        return ""
    return text.encode("latin-1", errors="replace").decode("latin-1")

# ----------------------------- Header ------------------------------
st.markdown(
    """
    <div style="background-color:#2e7d32;padding:15px;border-radius:6px;
                text-align:center;margin-bottom:20px;">
        <h1 style="color:white;margin:0;letter-spacing:3px;">FIELD REPORT</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------- 1. User Information -----------------------
st.subheader("1. User Information")
researcher = st.text_input("Researcher Name *")
title = st.text_input("Title of the Discovery *")
description = st.text_area("Description / Notes *")

# --------------------------- 2. GPS --------------------------------
st.subheader("2. GPS Location")
st.caption("Tap the location icon and allow your browser to share your position.")
location = streamlit_geolocation()

lat, lon = None, None
if location and location.get("latitude") is not None:
    lat = location["latitude"]
    lon = location["longitude"]
    st.success(f"📍 Coordinates: Lat {lat:.5f}, Lon {lon:.5f}")

    m = folium.Map(location=[lat, lon], zoom_start=16)
    folium.Marker(
        [lat, lon],
        popup="You are here",
        icon=folium.Icon(color="green"),
    ).add_to(m)
    st_folium(m, width=None, height=300, returned_objects=[])
else:
    st.info("Click the location icon above to capture your GPS coordinates.")

# --------------------- 3. Visual Evidence --------------------------
st.subheader("3. Visual Evidence")
photo = st.camera_input("Take a photo *")

# ------------------------ 4. Generate PDF --------------------------
st.subheader("4. Generate Report")

if st.button("Generate PDF Report", type="primary", use_container_width=True):
    missing = []
    if not researcher: missing.append("Researcher Name")
    if not title: missing.append("Title")
    if not description: missing.append("Description")
    if lat is None: missing.append("GPS Location")
    if photo is None: missing.append("Photo")

    if missing:
        st.error(f"⚠️ Please complete: {', '.join(missing)}")
    else:
        photo_path = None
        try:
            # Save the photo to a temp JPEG
            img = Image.open(photo)
            if img.mode != "RGB":
                img = img.convert("RGB")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                img.save(tmp.name, "JPEG", quality=85)
                photo_path = tmp.name

            # Build the PDF
            pdf = FPDF()
            pdf.add_page()

            # Green title banner
            pdf.set_fill_color(46, 125, 50)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 22)
            pdf.cell(0, 15, "FIELD REPORT",
                     new_x="LMARGIN", new_y="NEXT", align="C", fill=True)

            pdf.set_text_color(0, 0, 0)
            pdf.ln(8)

            # Researcher + Date row
            date_str = datetime.now().strftime("%d/%m/%Y")
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(30, 7, "Researcher:")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(100, 7, safe(researcher))
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(15, 7, "Date:")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, date_str, new_x="LMARGIN", new_y="NEXT")

            # Coordinates
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 7, f"Coordinates: Lat {lat:.5f}, Lon {lon:.5f}",
                     new_x="LMARGIN", new_y="NEXT")

            # Separator
            pdf.ln(2)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            # Finding (title)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, safe(f"Finding: {title}"),
                     new_x="LMARGIN", new_y="NEXT")

            # Observations
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Observations:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, safe(description))
            pdf.ln(4)

            # Photo, centered, scaled
            img_width = 120
            x_pos = (pdf.w - img_width) / 2
            pdf.image(photo_path, x=x_pos, w=img_width)

            # Output
            pdf_bytes = bytes(pdf.output())

            st.success("✅ Report generated!")
            st.download_button(
                "⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"field_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Something went wrong while generating the PDF: {e}")
        finally:
            if photo_path and os.path.exists(photo_path):
                try:
                    os.unlink(photo_path)
                except OSError:
                    pass
