# Internship Attendance System

SMART ATTENDANCE SYSTEM for School of Internal Security and SMART Policing, Rashtriya Raksha University

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)

## 🌐 Public Deployment

This app can be deployed publicly using Streamlit Cloud (recommended) or other platforms.

### Quick Deploy to Streamlit Cloud

1. **Fork this repository** to your GitHub account
2. **Go to [Streamlit Cloud](https://share.streamlit.io/)**
3. **Connect your GitHub account** and select this repository
4. **Deploy**: The app will automatically deploy with the provided configuration

### Manual Deployment

For other platforms, the app includes:
- `requirements.txt` - Python dependencies
- `runtime.txt` - Python version specification
- `.streamlit/config.toml` - Streamlit configuration

### Cloud Deployment Notes

- **Google Drive**: Disabled in cloud deployments for security. Images are stored locally.
- **Data Persistence**: Data is stored in the deployment environment and persists between sessions.
- **File Uploads**: All uploaded images are stored in the cloud environment.
- **Admin Access**: Default credentials work in cloud deployments.

## Features

## Features

- **📱 Mobile Compatible**: Optimized for Android and iOS devices
- **📝 User Registration**: Register interns with name, roll number, program, and group
- **📸 Attendance Marking**: Upload/capture photos with automatic GPS location tracking
- **👑 Admin Panel**: Manage groups, edit records, change password, export to Excel
- **☁️ Google Drive Integration**: Automatic photo upload to cloud storage
- **📍 GPS Location**: Accurate location tracking from photo EXIF data
- **📊 Dashboard & Reports**: KPI metrics, interactive filters, attendance-by-group charts, time-series charts, top attendees, GPS map, and CSV export

## Setup

1. Install dependencies:
   ```bash
   pip install streamlit pandas pillow geopy pydrive2 requests openpyxl
   ```

2. Run the application:
   ```bash
   streamlit run Code.py
   ```

3. Open your browser to `http://localhost:8501`

## Hosting / Deployment

### ✅ Recommended: Streamlit Community Cloud
1. Fork this repository to your GitHub account.
2. Go to https://share.streamlit.io/ and connect your GitHub account.
3. Click **New app** → select your fork, branch `main`, and `Code.py` as the file to run.
4. Click **Deploy** — your app will be public and automatically update on new commits.

Notes:
- If you need Google Drive integration, add the `client_secrets.json` contents to Streamlit **Secrets** (recommended) or upload it to the app root (use caution with sensitive files).

#### Streamlit Secrets (recommended)
In Streamlit Cloud, open your app settings → **Secrets** and add the following TOML to securely set admin credentials and Google Drive info.

Example:

```toml
# Admin credentials
[admin]
username = "your_admin_username"
password = "your_admin_password"

# Google Drive client secrets (as a JSON string) — paste the full client_secrets JSON here
[gdrive]
client_secrets = "{\"installed\": {\"client_id\": \"YOUR_CLIENT_ID\", ... }}"
```

- The app will read `admin` and `gdrive.client_secrets` from `st.secrets` on startup and create the necessary `admin_config.json` and `client_secrets.json` files automatically.
- **Do not** commit `client_secrets.json` or `mycreds.txt` to the repository — they are ignored in `.gitignore` for security.

### Alternative: Render / Railway / Other
- Create a new web service, point it to this repository, select Python, and set the build command to `pip install -r requirements.txt` and start command to `streamlit run Code.py --server.port $PORT`.
- Ensure `runtime.txt` pins Python version (already included).

### Local Docker (optional)
- Build a container and run it behind a reverse proxy if required.

---

## Mobile Usage

- **Navigation**: Use the Register and Admin buttons in the top right corner
- **Photo Capture**: Use your phone's camera to take photos with GPS data
- **Responsive Design**: Interface automatically adjusts for mobile screens

## Admin Features

### 👑 Full Data Management Authority

- **Group Management**: Add, rename, and delete groups
- **User Management**: Delete individual users or clear all registrations
- **Attendance Editing**: Delete specific attendance records
- **Column Management**: Remove unwanted columns from attendance data
- **Data Reset**: Complete system reset (deletes all data permanently)
- **Backup & Restore**: Export/import complete system backups
- **Statistics**: View database metrics and counts

### 🚨 Danger Zone Features

- **Reset All Data**: Permanently deletes ALL users, attendance records, and uploaded images
- **Clear All Users**: Removes all registered users
- **Remove Columns**: Delete specific data columns (with protection for essential fields)

### 📊 Advanced Operations

- **Export Backup**: Download complete ZIP backup of all data and images
- **Import Backup**: Restore system from ZIP backup file
- **Database Statistics**: Real-time metrics on users, records, and groups

## ⚠️ Admin Safety Notes

- **Backup First**: Always export a backup before using reset or deletion features
- **Confirmation Required**: Dangerous operations require explicit confirmation
- **Essential Columns Protected**: Core columns (Name, Roll_No, Group) cannot be deleted
- **Change Default Password**: Update admin credentials immediately after first login

## Default Admin Credentials

- Username: `sourav.dey`
- Password: `2233`

*Change the password after first login for security.*

## GPS Troubleshooting

If GPS coordinates are not being detected:
1. Ensure location services are enabled on your device
2. Allow camera access to location data
3. Take photos with GPS enabled
4. The app will show coordinates when available
