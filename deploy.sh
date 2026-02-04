#!/bin/bash

# Internship Attendance System - Deployment Script
# This script helps deploy the app to various platforms

echo "🚀 Internship Attendance System - Deployment Helper"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "Code.py" ]; then
    echo "❌ Error: Code.py not found. Please run this script from the project root directory."
    exit 1
fi

echo "📁 Project structure check:"
ls -la

echo ""
echo "Choose deployment platform:"
echo "1) Streamlit Cloud (Recommended - Free)"
echo "2) Heroku"
echo "3) Railway"
echo "4) Local testing only"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🌐 Streamlit Cloud Deployment"
        echo "============================="
        echo "To deploy to Streamlit Cloud:"
        echo "1. Go to https://share.streamlit.io/"
        echo "2. Connect your GitHub account"
        echo "3. Select this repository"
        echo "4. Click 'Deploy'"
        echo ""
        echo "The app will be publicly accessible at a share.streamlit.io URL"
        ;;

    2)
        echo "🐘 Heroku Deployment"
        echo "===================="
        echo "Creating Heroku deployment files..."

        # Create Procfile for Heroku
        echo "web: streamlit run Code.py --server.port \$PORT --server.headless true" > Procfile

        echo "✅ Created Procfile"
        echo ""
        echo "To deploy to Heroku:"
        echo "1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli"
        echo "2. Login: heroku login"
        echo "3. Create app: heroku create your-app-name"
        echo "4. Deploy: git push heroku main"
        echo ""
        echo "Your app will be available at: https://your-app-name.herokuapp.com"
        ;;

    3)
        echo "🚂 Railway Deployment"
        echo "====================="
        echo "To deploy to Railway:"
        echo "1. Go to https://railway.app/"
        echo "2. Connect your GitHub repository"
        echo "3. Railway will automatically detect and deploy the Streamlit app"
        echo ""
        echo "Railway will provide a public URL for your app"
        ;;

    4)
        echo "🏠 Local Testing"
        echo "================"
        echo "Running locally for testing..."
        echo "Make sure you have Python and dependencies installed:"
        echo "pip install -r requirements.txt"
        echo "streamlit run Code.py"
        ;;

    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment preparation complete!"
echo "📖 Check README.md for detailed instructions"
echo "🔐 Default admin credentials: sourav.dey / 2233"