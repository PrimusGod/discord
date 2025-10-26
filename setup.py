#!/usr/bin/env python3
"""
Pokemon Discord Bot Setup Script
This script helps set up the Pokemon Discord bot environment.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print("✅ Python version is compatible")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["data", "logs", "cogs", "database", "pokemon", "utils"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")

def setup_environment():
    """Setup environment variables"""
    print("\n🔧 Setting up environment...")
    
    # Check if .env exists
    if not Path(".env").exists():
        if Path(".env.example").exists():
            shutil.copy(".env.example", ".env")
            print("✅ Created .env file from .env.example")
            print("⚠️  Please edit .env file with your Discord bot token!")
        else:
            print("⚠️  Please create a .env file with your Discord bot token!")
    else:
        print("✅ .env file already exists")

def create_startup_script():
    """Create a startup script for easy launching"""
    print("\n🚀 Creating startup script...")
    
    if sys.platform == "win32":
        # Windows batch file
        with open("start_bot.bat", "w") as f:
            f.write("@echo off\n")
            f.write("echo Starting Pokemon Discord Bot...\n")
            f.write("python run_bot.py\n")
            f.write("pause\n")
        print("✅ Created start_bot.bat for Windows")
    else:
        # Unix shell script
        with open("start_bot.sh", "w") as f:
            f.write("#!/bin/bash\n")
            f.write("echo 'Starting Pokemon Discord Bot...'\n")
            f.write("python3 run_bot.py\n")
        os.chmod("start_bot.sh", 0o755)
        print("✅ Created start_bot.sh for Unix/Linux/Mac")

def main():
    """Main setup function"""
    print("🎮 Pokemon Discord Bot Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Create directories
    create_directories()
    
    # Setup environment
    setup_environment()
    
    # Create startup script
    create_startup_script()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit the .env file with your Discord bot token")
    print("2. Run the bot using one of these methods:")
    
    if sys.platform == "win32":
        print("   - Double-click start_bot.bat")
        print("   - Run: python run_bot.py")
    else:
        print("   - Run: ./start_bot.sh")
        print("   - Run: python3 run_bot.py")
    
    print("\n📚 For more information, check README.md")
    print("🌟 Enjoy your Pokemon Discord bot!")

if __name__ == "__main__":
    main()