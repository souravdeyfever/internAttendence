import streamlit as st
import pandas as pd
import os
import shutil
import zipfile
from PIL import Image, ExifTags
from datetime import datetime
import requests
from geopy.geocoders import Nominatim
import json
from io import BytesIO
import openpyxl
import warnings

# Suppress oauth2client warnings
warnings.filterwarnings("ignore", message="Cannot access mycreds.txt*", category=UserWarning)

# Check if running in cloud deployment
IS_CLOUD_DEPLOYMENT = os.getenv('STREAMLIT_SERVER_HEADLESS', 'false').lower() == 'true'

# ------------------------------------------------
# STREAMLIT CONFIGURATION (must be first)
# ------------------------------------------------
st.set_page_config(
    page_title="Internship Attendence",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Initialize session state at the very beginning
if "current_page" not in st.session_state:
    st.session_state.current_page = "attendance"
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "show_reset_confirm" not in st.session_state:
    st.session_state.show_reset_confirm = False

# ------------------------------------------------
# DIRECTORIES & DATABASES
# ------------------------------------------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

USERS_DB = "users_db.csv"
ATTEND_DB = "attendance_db.csv"
ADMIN_FILE = "admin_config.json"

# Create databases if not exist
if not os.path.exists(USERS_DB):
    pd.DataFrame(columns=["Name","Roll_No","Organisation","Group"]).to_csv(USERS_DB, index=False)

if not os.path.exists(ATTEND_DB):
    pd.DataFrame(columns=[
        "Group","Name","Roll_No",
        "Capture_Date","Capture_Time",
        "Latitude","Longitude",
        "Photo_Location","Upload_Location",
        "Image_File"
    ]).to_csv(ATTEND_DB, index=False)

# Default admin password file
if not os.path.exists(ADMIN_FILE):
    # Prefer Streamlit secrets in deployed environments
    try:
        secret_admin = st.secrets.get("admin", None)
    except Exception:
        secret_admin = None

    if secret_admin and isinstance(secret_admin, dict) and secret_admin.get("username") and secret_admin.get("password"):
        with open(ADMIN_FILE, "w") as f:
            json.dump({"username": secret_admin.get("username"), "password": secret_admin.get("password")}, f)
    else:
        # Create a safe placeholder - change in production or provide credentials via Streamlit Secrets
        with open(ADMIN_FILE, "w") as f:
            json.dump({"username": "admin", "password": "changeme"}, f)

# If GDrive client secrets are stored in Streamlit secrets (as a JSON string), write them to file so pydrive2 can use them
try:
    gdrive_secret = st.secrets.get("gdrive", None)
except Exception:
    gdrive_secret = None

if gdrive_secret and isinstance(gdrive_secret, dict) and gdrive_secret.get("client_secrets"):
    try:
        cs_content = gdrive_secret.get("client_secrets")
        if cs_content and not os.path.exists("client_secrets.json"):
            with open("client_secrets.json", "w") as f:
                f.write(cs_content)
    except Exception:
        pass

# ------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------

def dms_to_dd(dms):
    """Convert GPS coordinates from DMS (degrees, minutes, seconds) to DD (decimal degrees)"""
    try:
        if isinstance(dms, tuple) and len(dms) == 3:
            degrees = float(dms[0][0]) / float(dms[0][1]) if isinstance(dms[0], tuple) else float(dms[0])
            minutes = float(dms[1][0]) / float(dms[1][1]) if isinstance(dms[1], tuple) else float(dms[1])
            seconds = float(dms[2][0]) / float(dms[2][1]) if isinstance(dms[2], tuple) else float(dms[2])
            return degrees + (minutes / 60.0) + (seconds / 3600.0)
        else:
            # Handle cases where DMS might be stored as simple floats
            return float(dms)
    except (TypeError, ValueError, IndexError, ZeroDivisionError):
        return None

def get_exif_data(img):
    """Extract EXIF data including GPS coordinates from image"""
    try:
        exif_raw = img._getexif()
        if not exif_raw:
            return None, None, None

        exif = {ExifTags.TAGS.get(k, k): v for k, v in exif_raw.items()}
        capture_time = exif.get("DateTimeOriginal", exif.get("DateTime", None))

        gps = exif.get("GPSInfo", None)
        lat, lon = None, None

        if gps:
            gps_data = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps.items()}

            # Extract latitude
            if "GPSLatitude" in gps_data:
                lat = dms_to_dd(gps_data["GPSLatitude"])
                if gps_data.get("GPSLatitudeRef") == "S" and lat:
                    lat = -lat

            # Extract longitude
            if "GPSLongitude" in gps_data:
                lon = dms_to_dd(gps_data["GPSLongitude"])
                if gps_data.get("GPSLongitudeRef") == "W" and lon:
                    lon = -lon

        return capture_time, lat, lon
    except Exception as e:
        print(f"Error extracting EXIF data: {e}")
        return None, None, None

def reverse_geocode(lat, lon):
    try:
        geolocator = Nominatim(user_agent="attendance_app")
        loc = geolocator.reverse(f"{lat},{lon}", language="en")
        return loc.address if loc else "Unknown"
    except:
        return "Unknown"

def get_upload_location():
    try:
        ip = requests.get("https://api64.ipify.org?format=json").json()["ip"]
        info = requests.get(f"https://ipinfo.io/{ip}/json").json()
        return f"{info.get('city','Unknown')}, {info.get('region','Unknown')}"
    except:
        return "Unknown"

def load_admin():
    with open(ADMIN_FILE) as f:
        return json.load(f)

def save_admin(user,pwd):
    with open(ADMIN_FILE,"w") as f:
        json.dump({"username":user,"password":pwd}, f)

def dataframe_to_excel_bytes(df):
    """Convert pandas DataFrame to Excel file bytes"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance')
    output.seek(0)
    return output.getvalue()

# ------------------------------------------------
# STREAMLIT UI
# ------------------------------------------------

# Main Title and Subtitle
st.title("Internship Attendence")
st.subheader("School of Internal Security and SMART Policing, Rashtriya Raksha University")

# Initialize current page if not set
if "current_page" not in st.session_state:
    st.session_state.current_page = "attendance"

# Top navigation bar with Register and Admin in top right
col1, col2, col3 = st.columns([1, 1, 2])  # Left space, center space, right space

with col3:
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("📝 Register", key="nav_register", use_container_width=True):
            st.session_state.current_page = "register"
    with nav_col2:
        if st.button("👑 Admin", key="nav_admin", use_container_width=True):
            st.session_state.current_page = "admin"

# Add back button for register and admin pages
if st.session_state.current_page in ["register", "admin"]:
    if st.button("⬅️ Back to Attendance", key="back_button"):
        st.session_state.current_page = "attendance"
        st.rerun()

# Main content area
if st.session_state.current_page == "register":
    # ------------------------------------------------
    # REGISTRATION PAGE
    # ------------------------------------------------
    st.header("📝 User Registration")

    # Mobile-friendly layout
    col1, col2 = st.columns([1, 1]) if st.session_state.get("is_mobile", False) else st.columns([1, 1])

    with col1:
        name = st.text_input("Full Name", key="reg_name")
        roll = st.text_input("Roll Number", key="reg_roll")

    with col2:
        orgs = ["BASM4","BASM2","MAPA2","MAPA4","BASM6","BASM3"]
        org = st.selectbox("Program", orgs, key="reg_org")

        users = pd.read_csv(USERS_DB)
        groups = users["Group"].dropna().unique().tolist()
        groups.append("Create New Group")
        group = st.selectbox("Group", groups, key="reg_group")

    if group == "Create New Group":
        group_name = st.text_input("Enter new group name", key="reg_new_group")
    else:
        group_name = group

    # Center the register button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Register", use_container_width=True):
            # Validation
            if not name.strip():
                st.error("Please enter a full name")
            elif not roll.strip():
                st.error("Please enter a roll number")
            elif group == "Create New Group" and not group_name.strip():
                st.error("Please enter a new group name")
            elif users[(users["Name"] == name.strip()) & (users["Roll_No"] == roll.strip())].shape[0] > 0:
                st.error("User with this name and roll number already exists")
            else:
                df = pd.read_csv(USERS_DB)
                final_group = group_name.strip()
                new = pd.DataFrame([[name.strip(), roll.strip(), org, final_group]], columns=df.columns)
                df = pd.concat([df, new], ignore_index=True)
                df.to_csv(USERS_DB, index=False)
                st.success("Registered Successfully!")
                st.rerun()

elif st.session_state.current_page == "admin":
    # ------------------------------------------------
    # ADMIN PANEL
    # ------------------------------------------------
    st.header("👑 Admin Panel")

    admin = load_admin()

    if not st.session_state.admin_logged_in:
        # Login form
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("Admin Login")
            user = st.text_input("Username", key="admin_user")
            pwd = st.text_input("Password", type="password", key="admin_pwd")

            if st.button("Login", use_container_width=True):
                if user == admin["username"] and pwd == admin["password"]:
                    st.session_state.admin_logged_in = True
                    st.success("Admin Access Granted")
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
    else:
        st.success("Admin Access Granted")

        # Logout button
        if st.button("Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

        # ---------- GROUP MANAGEMENT ----------
        st.markdown("### 🔧 Manage Groups")

        users_df = pd.read_csv(USERS_DB)

        # Add new group
        new_group = st.text_input("Add new group", key="new_group_input")
        if st.button("Add Group"):
            if new_group.strip():
                users_df.loc[len(users_df)] = ["","","",new_group.strip()]
                users_df.to_csv(USERS_DB, index=False)
                st.success("Group added!")
                st.rerun()
            else:
                st.error("Please enter a group name")

        # Rename group
        if not users_df.empty and "Group" in users_df.columns:
            available_groups = users_df["Group"].dropna().unique().tolist()
            if available_groups:
                col1, col2 = st.columns(2)
                with col1:
                    old = st.selectbox("Select group to rename", available_groups, key="rename_old")
                with col2:
                    new = st.text_input("New group name", key="rename_new")

                if st.button("Rename Group"):
                    if new.strip() and new.strip() != old:
                        users_df["Group"] = users_df["Group"].replace(old, new.strip())
                        users_df.to_csv(USERS_DB, index=False)
                        st.success("Group renamed!")
                        st.rerun()
                    elif new.strip() == old:
                        st.error("New group name must be different from current name")
                    else:
                        st.error("Please enter a new group name")

        # Delete group
        if not users_df.empty and "Group" in users_df.columns:
            available_groups = users_df["Group"].dropna().unique().tolist()
            if available_groups:
                delg = st.selectbox("Select group to delete", available_groups, key="delete_group")
                if st.button("Delete Group"):
                    # Check if group has users
                    users_in_group = len(users_df[users_df["Group"] == delg])
                    if users_in_group > 0:
                        st.error(f"Cannot delete group '{delg}' - it contains {users_in_group} user(s). Remove users first.")
                    else:
                        users_df = users_df[users_df["Group"] != delg]
                        users_df.to_csv(USERS_DB, index=False)
                        st.success("Group deleted!")
                        st.rerun()

        # ---------- EDIT ATTENDANCE ----------
        st.markdown("### 📊 Edit Attendance Records")
        att = pd.read_csv(ATTEND_DB)
        if not att.empty:
            st.dataframe(att, use_container_width=True)

            # Only show delete option if there are records
            if len(att) > 0:
                row_id = st.number_input("Enter row index to delete", min_value=0, max_value=len(att)-1, step=1, key="delete_row_id")
                if st.button("Delete Row"):
                    try:
                        att = att.drop(index=row_id)
                        att.to_csv(ATTEND_DB, index=False)
                        st.success("Row deleted!")
                        st.rerun()
                    except KeyError:
                        st.error(f"Row {row_id} does not exist")
        else:
            st.info("No attendance records found")

        # ---------- CHANGE PASSWORD ----------
        st.markdown("### 🔐 Change Admin Password")
        newpwd = st.text_input("New Password", type="password", key="new_password")
        if st.button("Update Password"):
            if newpwd.strip():
                save_admin(admin["username"], newpwd.strip())
                st.success("Password updated!")
                st.rerun()
            else:
                st.error("Please enter a password")

        # ---------- DOWNLOAD EXCEL ----------
        if not att.empty:
            excel_data = dataframe_to_excel_bytes(att)
            st.download_button(
                "Download Attendance Excel",
                excel_data,
                file_name="attendance.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # ---------- DATA MANAGEMENT ----------
        st.markdown("### 💾 Data Management")

        # Reset All Data
        st.markdown("#### 🚨 Reset All Data")
        st.warning("⚠️ **DANGER ZONE**: This will permanently delete ALL data!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Reset All Data", key="reset_all", use_container_width=True, type="secondary"):
                # Create confirmation dialog
                st.session_state.show_reset_confirm = True

        if st.session_state.get("show_reset_confirm", False):
            st.error("🔴 **FINAL CONFIRMATION**: This will delete ALL users, attendance records, and uploaded images!")
            confirm_col1, confirm_col2 = st.columns(2)
            with confirm_col1:
                if st.button("✅ YES, DELETE EVERYTHING", key="confirm_reset", use_container_width=True, type="primary"):
                    # Delete all CSV files
                    if os.path.exists(USERS_DB):
                        os.remove(USERS_DB)
                    if os.path.exists(ATTEND_DB):
                        os.remove(ATTEND_DB)

                    # Delete uploads directory and contents
                    if os.path.exists(UPLOAD_DIR):
                        import shutil
                        shutil.rmtree(UPLOAD_DIR)
                        os.makedirs(UPLOAD_DIR, exist_ok=True)

                    # Recreate empty databases
                    pd.DataFrame(columns=["Name","Roll_No","Organisation","Group"]).to_csv(USERS_DB, index=False)
                    pd.DataFrame(columns=[
                        "Group","Name","Roll_No",
                        "Capture_Date","Capture_Time",
                        "Latitude","Longitude",
                        "Photo_Location","Upload_Location",
                        "Image_File"
                    ]).to_csv(ATTEND_DB, index=False)

                    st.session_state.show_reset_confirm = False
                    st.success("✅ All data has been permanently deleted and databases reset!")
                    st.rerun()

            with confirm_col2:
                if st.button("❌ CANCEL", key="cancel_reset", use_container_width=True):
                    st.session_state.show_reset_confirm = False
                    st.info("Reset cancelled.")
                    st.rerun()

        # Remove Registration Data
        st.markdown("#### 👥 Remove Registration Data")
        users_df = pd.read_csv(USERS_DB)
        if not users_df.empty:
            st.markdown("**Current Users:**")
            st.dataframe(users_df, use_container_width=True)

            # Delete specific user
            if len(users_df) > 0:
                user_options = [f"{row['Name']} ({row['Roll_No']}) - {row['Group']}" for _, row in users_df.iterrows()]
                selected_user = st.selectbox("Select user to delete", user_options, key="delete_user_select")
                if st.button("Delete Selected User", key="delete_user"):
                    # Find and delete the user
                    user_index = user_options.index(selected_user)
                    users_df = users_df.drop(index=user_index)
                    users_df.to_csv(USERS_DB, index=False)
                    st.success("User deleted successfully!")
                    st.rerun()

            # Clear all users
            st.markdown("---")
            st.warning("This will delete ALL registered users!")
            if st.button("Clear All Users", key="clear_all_users", use_container_width=True, type="secondary"):
                pd.DataFrame(columns=["Name","Roll_No","Organisation","Group"]).to_csv(USERS_DB, index=False)
                st.success("All users have been deleted!")
                st.rerun()
        else:
            st.info("No users registered yet.")

        # Remove Column
        st.markdown("#### 📊 Remove Column")
        att_df = pd.read_csv(ATTEND_DB)
        if not att_df.empty:
            st.markdown("**Current Attendance Columns:**")
            st.write(list(att_df.columns))

            available_columns = [col for col in att_df.columns if col not in ["Group", "Name", "Roll_No"]]  # Keep essential columns
            if available_columns:
                column_to_remove = st.selectbox("Select column to remove", available_columns, key="remove_column_select")
                if st.button("Remove Column", key="remove_column"):
                    if column_to_remove in att_df.columns:
                        att_df = att_df.drop(columns=[column_to_remove])
                        att_df.to_csv(ATTEND_DB, index=False)
                        st.success(f"Column '{column_to_remove}' has been removed!")
                        st.rerun()
                    else:
                        st.error("Column not found!")
            else:
                st.info("No removable columns available (essential columns protected).")
        else:
            st.info("No attendance records found.")

        # ---------- ADVANCED DATA OPERATIONS ----------
        st.markdown("### 🔧 Advanced Operations")

        # Bulk operations
        st.markdown("#### 📋 Bulk Operations")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Export All Data (ZIP)", key="export_all", use_container_width=True):
                import zipfile
                import io

                # Create ZIP file in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add CSV files
                    if os.path.exists(USERS_DB):
                        zip_file.write(USERS_DB, 'users_db.csv')
                    if os.path.exists(ATTEND_DB):
                        zip_file.write(ATTEND_DB, 'attendance_db.csv')
                    if os.path.exists(ADMIN_FILE):
                        zip_file.write(ADMIN_FILE, 'admin_config.json')

                    # Add images if they exist
                    if os.path.exists(UPLOAD_DIR):
                        for root, dirs, files in os.walk(UPLOAD_DIR):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.join('uploads', file)
                                zip_file.write(file_path, arcname)

                zip_buffer.seek(0)
                st.download_button(
                    "Download Complete Backup (ZIP)",
                    zip_buffer.getvalue(),
                    file_name="attendance_system_backup.zip",
                    mime="application/zip",
                    use_container_width=True
                )

        with col2:
            uploaded_backup = st.file_uploader("Import Backup (ZIP)", type=["zip"], key="import_backup")
            if uploaded_backup and st.button("Import Data", key="import_data", use_container_width=True):
                try:
                    import zipfile
                    with zipfile.ZipFile(uploaded_backup, 'r') as zip_file:
                        # Extract files
                        zip_file.extractall('.')

                    st.success("Data imported successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")

        # Database Statistics
        st.markdown("#### 📈 Database Statistics")
        users_count = len(pd.read_csv(USERS_DB)) if os.path.exists(USERS_DB) else 0
        attendance_count = len(pd.read_csv(ATTEND_DB)) if os.path.exists(ATTEND_DB) else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", users_count)
        with col2:
            st.metric("Total Attendance Records", attendance_count)
        with col3:
            groups_count = len(pd.read_csv(USERS_DB)["Group"].dropna().unique()) if users_count > 0 else 0
            st.metric("Total Groups", groups_count)

else:  # Default to attendance page
    # ------------------------------------------------
    # ATTENDANCE PAGE
    # ------------------------------------------------
    st.header("📸 Mark Attendance")

    users = pd.read_csv(USERS_DB)

    # Check if users database is empty
    if users.empty:
        st.warning("No users registered yet. Please register users first using the Register button above.")
        st.stop()

    # Get available groups, filter out NaN values
    available_groups = users["Group"].dropna().unique().tolist()
    if not available_groups:
        st.warning("No groups found. Please register users with groups first.")
        st.stop()

    # Mobile-friendly layout for attendance
    col1, col2 = st.columns([1, 1]) if st.session_state.get("is_mobile", False) else st.columns([1, 1])

    with col1:
        sel_group = st.selectbox("Select Group", available_groups, key="attendance_group")

    with col2:
        # Get names for selected group
        group_users = users[users["Group"] == sel_group]
        if group_users.empty:
            st.warning(f"No users found in group '{sel_group}'. Please register users for this group.")
            st.stop()

        available_names = group_users["Name"].dropna().unique().tolist()
        if not available_names:
            st.warning(f"No valid names found in group '{sel_group}'. Please check user registrations.")
            st.stop()

        sel_name = st.selectbox("Select Name", available_names, key="attendance_name")

    # Verify the selected user still exists (in case of concurrent modifications)
    selected_user = users[(users["Group"] == sel_group) & (users["Name"] == sel_name)]
    if selected_user.empty:
        st.error(f"Selected user '{sel_name}' in group '{sel_group}' not found. Please refresh and try again.")
        st.stop()

    # File uploader with mobile-friendly settings
    uploaded = st.file_uploader(
        "Upload or Capture Image",
        type=["jpg","jpeg","png"],
        help="Take a photo or upload an image file"
    )

    if uploaded:
        img = Image.open(uploaded)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get roll number safely
        try:
            roll_no = selected_user["Roll_No"].iloc[0]
        except (IndexError, KeyError):
            st.error("Error retrieving user information. Please try again.")
            st.stop()

        filename = f"{sel_name}_{roll_no}_{ts}.jpg"
        local_path = os.path.join(UPLOAD_DIR, filename)
        img.save(local_path)

        cap_time, lat, lon = get_exif_data(img)

        if cap_time:
            cap_date = cap_time.split(" ")[0].replace(":","-")
            cap_clock = cap_time.split(" ")[1]
        else:
            cap_date = datetime.now().date()
            cap_clock = datetime.now().time()

        photo_loc = reverse_geocode(lat, lon) if lat and lon else "Unknown"
        upload_loc = get_upload_location()

        # Mobile-friendly image display
        col1, col2 = st.columns([1, 2])
        with col1:
            # Smaller image for mobile
            img_width = 200 if st.session_state.get("is_mobile", False) else 300
            st.image(img, width=img_width, caption="Uploaded Image")

        with col2:
            st.write("📍 **Photo Location:**", photo_loc)
            st.write("📡 **Upload Location:**", upload_loc)
            if lat and lon:
                st.write(f"📌 **Coordinates:** {lat:.6f}, {lon:.6f}")
            else:
                st.warning("No GPS data found in image. Location tracking unavailable.")

        # Center the submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Submit Attendance", use_container_width=True):
                df = pd.read_csv(ATTEND_DB)
                new_row = pd.DataFrame([[
                    sel_group, sel_name, roll_no,
                    cap_date, cap_clock,
                    lat, lon,
                    photo_loc, upload_loc,
                    filename
                ]], columns=df.columns)

                df = pd.concat([df,new_row], ignore_index=True)
                df.to_csv(ATTEND_DB, index=False)
                st.success("Attendance Recorded & Image Uploaded!")

