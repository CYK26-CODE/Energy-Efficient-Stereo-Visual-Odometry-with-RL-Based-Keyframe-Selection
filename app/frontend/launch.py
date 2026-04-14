#!/usr/bin/env python3
"""
DQN SLAM Training System - Application Launcher
Handles dependencies and starts the main dashboard
"""

import subprocess
import sys
import os
from pathlib import Path


class DependencyManager:
    """Manage Python package dependencies"""
    
    REQUIRED_PACKAGES = {
        'customtkinter': 'customtkinter',
        'cv2': 'opencv-python==4.12.0.88',
        'numpy': 'numpy>=2.2.0',
        'PIL': 'pillow>=10.0.0',
        'matplotlib': 'matplotlib>=3.10.0',
        'torch': 'torch',  # Install pytorch separately
        'scipy': 'scipy>=1.16.0',
        'sklearn': 'scikit-learn>=1.7.0',
        'psutil': 'psutil>=7.1.0',
        'requests': 'requests>=2.32.0'
    }
    
    @staticmethod
    def check_and_install():
        """Check and install required packages"""
        print("=" * 60)
        print("🔍 DEPENDENCY VERIFICATION")
        print("=" * 60)
        
        missing_packages = []
        
        for import_name, pip_name in DependencyManager.REQUIRED_PACKAGES.items():
            try:
                __import__(import_name)
                print(f"✅ {import_name:<20} - installed")
            except ImportError:
                print(f"❌ {import_name:<20} - missing")
                missing_packages.append(pip_name)
        
        if missing_packages:
            print("\n" + "=" * 60)
            print("📦 INSTALLING MISSING PACKAGES")
            print("=" * 60)
            
            for package in missing_packages:
                print(f"\n📥 Installing {package}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    print(f"✅ {package} installed successfully")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️ Warning: Failed to install {package}")
                    print(f"   You may need to install it manually with:")
                    print(f"   pip install {package}")
        
        print("\n" + "=" * 60)
        print("✅ DEPENDENCY CHECK COMPLETE")
        print("=" * 60)


class DirectoryValidator:
    """Validate directory structure"""
    
    @staticmethod
    def validate():
        """Validate required directories exist"""
        print("\n" + "=" * 60)
        print("📁 DIRECTORY STRUCTURE VALIDATION")
        print("=" * 60)
        
        current_dir = Path(__file__).parent
        print(f"\n📍 Current directory: {current_dir}")
        project_root = current_dir.parent.parent
        
        required_dirs = {
            "app/backend": "Backend training modules",
            "app/frontend": "Frontend UI modules"
        }
        
        missing_dirs = []
        
        for dir_name, description in required_dirs.items():
            dir_path = project_root / Path(dir_name)
            if dir_path.exists():
                print(f"✅ {dir_name:<20} - {description}")
            else:
                print(f"⚠️ {dir_name:<20} - {description} (NOT FOUND)")
                missing_dirs.append((dir_name, description))
        
        if missing_dirs:
            print("\n⚠️ WARNING: Some directories are missing!")
            print("The application may not function properly.")
        
        return len(missing_dirs) == 0


class EnvironmentSetup:
    """Set up Python environment"""
    
    @staticmethod
    def setup():
        """Set up environment variables and paths"""
        print("\n" + "=" * 60)
        print("⚙️ ENVIRONMENT CONFIGURATION")
        print("=" * 60)
        
        # Set project root
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        
        # Add to Python path
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            print(f"✅ Added to PYTHONPATH: {project_root}")
        
        # Create logs directory if needed
        logs_dir = project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        print(f"✅ Logs directory ready: {logs_dir}")
        
        # Create models directory
        models_dir = project_root / "models"
        models_dir.mkdir(exist_ok=True)
        print(f"✅ Models directory ready: {models_dir}")
        
        print("\n✅ Environment configured")


class ApplicationLauncher:
    """Launch the main application"""
    
    @staticmethod
    def launch():
        """Start the main dashboard"""
        print("\n" + "=" * 60)
        print("🚀 LAUNCHING DQN SLAM TRAINING SYSTEM")
        print("=" * 60)
        
        frontend_dir = Path(__file__).parent
        main_script = frontend_dir / "main_dashboard.py"
        
        if not main_script.exists():
            print(f"\n❌ ERROR: Main script not found at {main_script}")
            return False
        
        try:
            print(f"\n▶️  Starting main dashboard...")
            print(f"   Script: {main_script}")
            
            # Import and run directly
            os.chdir(str(frontend_dir))
            
            # Add frontend to path
            sys.path.insert(0, str(frontend_dir))
            
            # Import main dashboard
            from main_dashboard import AdvancedDQNTrainingDashboard
            
            print("\n✅ Dashboard imported successfully")
            print("\n" + "=" * 60)
            print("📊 DASHBOARD STARTING")
            print("=" * 60)
            
            app = AdvancedDQNTrainingDashboard()
            app.mainloop()
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR starting dashboard: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main launcher function"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  🤖 DQN SLAM Training System - Application Launcher  ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Step 1: Validate Python version
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 8):
        print(f"❌ ERROR: Python 3.8+ required (found {sys.version_info.major}.{sys.version_info.minor})")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Step 2: Check dependencies
    try:
        DependencyManager.check_and_install()
    except Exception as e:
        print(f"\n⚠️ Error during dependency check: {e}")
        print("Continuing anyway...")
    
    # Step 3: Validate directory structure
    try:
        DirectoryValidator.validate()
    except Exception as e:
        print(f"⚠️ Warning: {e}")
    
    # Step 4: Set up environment
    try:
        EnvironmentSetup.setup()
    except Exception as e:
        print(f"⚠️ Warning during environment setup: {e}")
    
    # Step 5: Launch application
    print()
    success = ApplicationLauncher.launch()
    
    # Exit
    if success:
        print("\n✅ Application closed successfully")
        return 0
    else:
        print("\n❌ Application failed to start")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
