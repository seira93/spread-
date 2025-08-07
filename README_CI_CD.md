# 🚀 CI/CD Windows Build System

## 📋 Overview

This project uses GitHub Actions to automatically build Windows executables in a clean, controlled environment.

## 🔧 Features

- ✅ **Automated Windows Builds**: Every push to main/master triggers a build
- ✅ **Manual Builds**: On-demand builds via GitHub Actions
- ✅ **Release Management**: Automatic release creation with artifacts
- ✅ **Artifact Storage**: Built packages available for download
- ✅ **Version Control**: Tagged releases with build information

## 🚀 How to Use

### Method 1: Automatic Build (Recommended)

1. **Push to main branch**
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

2. **Check GitHub Actions**
   - Go to your repository on GitHub
   - Click "Actions" tab
   - Monitor the build progress

3. **Download the build**
   - Once complete, go to the Actions tab
   - Click on the completed workflow
   - Download the "Windows-Package" artifact

### Method 2: Manual Build

1. **Trigger manual build**
   - Go to your repository on GitHub
   - Click "Actions" tab
   - Select "Manual Windows Build"
   - Click "Run workflow"
   - Choose build type and click "Run workflow"

2. **Download the build**
   - Wait for build completion
   - Download the artifact from the Actions page

### Method 3: Release Build

1. **Create a release**
   - Go to "Releases" in your repository
   - Click "Create a new release"
   - Tag version (e.g., v1.0.0)
   - Publish release

2. **Download from releases**
   - The Windows package will be attached to the release
   - Download directly from the releases page

## 📁 Build Artifacts

Each build creates:
```
GoogleDriveDownloaderWeb_Package_Windows/
├── GoogleDriveDownloaderWeb.exe    # Windows executable
├── start_application.bat           # Launch script
├── client_secret.json              # Google API credentials
├── README.md                       # Documentation
├── README_WINDOWS.md              # Windows-specific guide
├── USAGE_GUIDE.md                 # Usage instructions
└── request.py                         # Original script
```

## 🔧 Build Configuration

### Environment
- **OS**: Windows Server 2022
- **Python**: 3.11
- **PyInstaller**: 6.15.0

### Build Command
```bash
pyinstaller --onefile --console --name=GoogleDriveDownloaderWeb \
  --add-data=README.md:. \
  --add-data=USAGE_GUIDE.md:. \
  --add-data=request.py:. \
  --exclude-module=backports \
  --exclude-module=jaraco \
  --exclude-module=pkg_resources \
  --exclude-module=tkinter \
  --exclude-module=matplotlib \
  --exclude-module=numpy \
  simple_gui.py
```

## 📊 Build Status

### Current Status
- ✅ **Automatic builds**: Working
- ✅ **Manual builds**: Working
- ✅ **Release builds**: Working
- ✅ **Artifact storage**: Working

### Build Times
- **Average build time**: 5-8 minutes
- **Artifact size**: ~25MB
- **Retention**: 30 days for manual builds

## 🔍 Troubleshooting

### Build Failures

1. **Dependency issues**
   - Check `requirements_windows.txt`
   - Update version constraints if needed

2. **PyInstaller errors**
   - Verify Python version compatibility
   - Check excluded modules

3. **File not found errors**
   - Ensure all required files are in repository
   - Check file paths in build script

### Common Issues

1. **Large build size**
   - Review excluded modules
   - Optimize dependencies

2. **Build timeout**
   - Increase timeout in workflow
   - Optimize build process

3. **Artifact download issues**
   - Check file size limits
   - Verify download permissions

## 📞 Support

### Getting Help

1. **Check Actions logs**
   - Go to Actions tab
   - Click on failed workflow
   - Review error messages

2. **Create an issue**
   - Use the build request template
   - Include error logs
   - Specify build type

3. **Contact maintainer**
   - For urgent issues
   - Include build ID and logs

## 🆕 Recent Updates

### v1.0.0
- Initial CI/CD setup
- Automated Windows builds
- Release management
- Artifact storage

### Future Plans
- [ ] Multi-platform builds (macOS, Linux)
- [ ] Automated testing
- [ ] Code signing
- [ ] Delta updates

## 📄 License

This CI/CD system is part of the main project and follows the same license terms. 