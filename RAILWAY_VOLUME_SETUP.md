# Railway /data Volume Configuration for Biped Platform

## 🎯 Overview

This document outlines the configuration for using Railway's persistent `/data` volume with the Biped Platform. The volume provides persistent storage for database files, uploads, logs, and backups that survive container restarts and deployments.

## 📁 Volume Structure

```
/data/
├── biped.db              # SQLite database (if not using PostgreSQL)
├── uploads/              # User uploaded files
│   ├── images/          # Profile images, portfolio images
│   ├── documents/       # PDF documents, contracts
│   ├── portfolios/      # Portfolio files
│   └── profiles/        # Profile pictures
├── logs/                # Application logs
└── backups/             # Database backups
```

## ⚙️ Configuration Files

### 1. railway.toml
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn --bind 0.0.0.0:$PORT backend.src.main:app"
healthcheckPath = "/api/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"

[env]
DATA_DIR = "/data"
PYTHONPATH = "/app"
```

### 2. nixpacks.toml
```toml
[start]
cmd = "gunicorn --bind 0.0.0.0:$PORT backend.src.main:app"

[variables]
PYTHONPATH = "/app"
DATA_DIR = "/data"

[phases.setup]
cmds = [
  "mkdir -p /data/uploads",
  "mkdir -p /data/logs", 
  "mkdir -p /data/backups",
  "chmod 755 /data"
]
```

### 3. Dockerfile
The Dockerfile includes proper volume setup and entrypoint script for robust deployment.

## 🔧 Application Features

### Storage Management API
- **GET** `/api/storage/info` - Get storage usage information
- **POST** `/api/storage/upload` - Upload files to persistent storage
- **GET** `/api/storage/file/<path>` - Serve files from storage
- **DELETE** `/api/storage/file/<path>` - Delete files from storage
- **GET** `/api/storage/files` - List files in storage
- **POST** `/api/storage/backup` - Create database backup
- **GET** `/api/storage/health` - Check storage system health

### Database Configuration
- **PostgreSQL**: Uses Railway's managed PostgreSQL when `DATABASE_URL` is provided
- **SQLite Fallback**: Uses `/data/biped.db` for persistent SQLite storage
- **Local Development**: Falls back to local `./data/` directory when `/data` is not accessible

### File Upload Handling
- Secure filename processing
- Timestamp-based naming to prevent conflicts
- Category-based organization (images, documents, portfolios, profiles)
- Automatic directory creation
- File size limits (16MB default)

## 🚀 Deployment Steps

### 1. Railway Dashboard Setup
1. Go to your Railway project dashboard
2. Navigate to the service settings
3. Add a volume at path `/data`
4. Set environment variables:
   - `DATA_DIR=/data`
   - `PYTHONPATH=/app`

### 2. Deploy Application
```bash
# Commit and push changes
git add .
git commit -m "🗄️ Add /data volume support with persistent storage"
git push origin main
```

### 3. Verify Deployment
1. Check Railway logs for successful startup
2. Test health endpoint: `https://your-app.railway.app/api/health`
3. Test storage health: `https://your-app.railway.app/api/storage/health`

## 🔍 Monitoring & Maintenance

### Storage Health Check
```bash
curl https://your-app.railway.app/api/storage/health
```

Expected response:
```json
{
  "success": true,
  "data": {
    "storage_accessible": true,
    "write_access": true,
    "data_directory": "/data",
    "storage_info": {
      "total_size_mb": 15.2,
      "file_count": 42,
      "directories": {
        "uploads": 25,
        "logs": 10,
        "backups": 7
      }
    }
  }
}
```

### Database Backup
```bash
curl -X POST https://your-app.railway.app/api/storage/backup
```

### File Upload Example
```bash
curl -X POST \
  -F "file=@example.jpg" \
  -F "category=images" \
  https://your-app.railway.app/api/storage/upload
```

## 🛠️ Troubleshooting

### Common Issues

1. **Permission Denied on /data**
   - Ensure the volume is properly mounted in Railway
   - Check container permissions
   - Application falls back to local directory in development

2. **Database Connection Issues**
   - Verify `DATABASE_URL` environment variable
   - Check PostgreSQL service status in Railway
   - SQLite fallback uses `/data/biped.db`

3. **File Upload Failures**
   - Check file size limits (16MB default)
   - Verify `/data/uploads` directory permissions
   - Monitor storage usage

### Logs and Debugging
```bash
# Check application logs
railway logs

# Check storage directory
railway shell
ls -la /data/
```

## 📊 Benefits

1. **Persistent Storage**: Files and database survive deployments
2. **Scalable**: Easy to monitor and manage storage usage
3. **Organized**: Structured directory layout for different file types
4. **Backup Ready**: Automated backup capabilities
5. **Development Friendly**: Graceful fallback for local development
6. **Production Ready**: Robust error handling and monitoring

## 🔐 Security Considerations

- Secure filename processing prevents directory traversal
- File type validation (implement as needed)
- Access control for sensitive files
- Regular backup rotation
- Storage usage monitoring to prevent abuse

## 📈 Future Enhancements

- File compression for storage optimization
- CDN integration for faster file serving
- Automated backup scheduling
- File versioning system
- Advanced file type validation
- Storage usage alerts and quotas

