# 🎬 BinhoCut - AI Video Editor

**Professional AI-powered video editing platform for social media content creators.**

## 🚀 Features

- ✅ **AI-Powered Video Cutting** - Automatic detection of best moments
- ✅ **Smart Subtitles** - Auto-generated, customizable subtitles
- ✅ **Multi-User Support** - Full authentication and subscription system
- ✅ **Async Processing** - Celery-based queue for scalability
- ✅ **Cloud Storage** - S3 integration for large-scale deployments
- ✅ **Analytics Dashboard** - Comprehensive usage and performance metrics
- ✅ **REST API** - Complete API for integrations
- ✅ **Stripe Integration** - Ready for monetization

---

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 15+
- Redis 7+
- FFmpeg
- Docker (optional, recommended)

---

## 🛠️ Installation

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/binhocut.git
cd binhocut

# 2. Create .env file
cp .env.example .env
# Edit .env with your configuration

# 3. Start all services
docker-compose -f docker/docker-compose.yml up -d

# 4. Run database migrations
docker-compose -f docker/docker-compose.yml exec web flask db upgrade

# 5. Create admin user (optional)
docker-compose -f docker/docker-compose.yml exec web python scripts/create_admin.py
```

**Access:**
- Web App: http://localhost
- API: http://localhost/api
- Flower (Celery Monitor): http://localhost:5555

### Option 2: Local Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements/development.txt

# 3. Setup PostgreSQL
createdb binhocut

# 4. Setup environment
cp .env.example .env
# Edit .env with your database URL

# 5. Run migrations
flask db upgrade

# 6. Start Redis
redis-server

# 7. Start Celery worker (in separate terminal)
celery -A celery_worker.celery worker --loglevel=info

# 8. Start Flask app
python run.py
```

---

## 🗄️ Database Migrations

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

---

## 🔧 Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/binhocut

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_BUCKET_NAME=your-bucket

# Stripe (for payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...

# SendGrid (for emails)
SENDGRID_API_KEY=SG...
```

### Subscription Plans

Edit plans in `config/development.py`:

```python
PLANS = {
    'free': {
        'videos_per_month': 5,
        'max_video_duration': 600,  # 10 minutes
        'max_clips_per_video': 3
    },
    'pro': {
        'videos_per_month': 50,
        'max_video_duration': 3600,  # 1 hour
        'max_clips_per_video': 10
    }
}
```

---

## 📡 API Documentation

### Authentication

```bash
# Register
POST /api/auth/register
{
  "email": "user@example.com",
  "username": "user123",
  "password": "securepass"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "securepass"
}
# Returns: { "access_token": "..." }
```

### Videos

```bash
# Upload video
POST /api/videos/upload
Headers: Authorization: Bearer <token>
Body: multipart/form-data (video file)

# Start processing
POST /api/videos/<id>/process
Headers: Authorization: Bearer <token>
Body: {
  "mode": "auto",
  "num_clips": 3,
  "with_subtitles": true
}

# Get status
GET /api/videos/<id>/status
Headers: Authorization: Bearer <token>

# List videos
GET /api/videos?page=1&per_page=20
Headers: Authorization: Bearer <token>
```

### Clips

```bash
# Download clip
GET /api/clips/<id>/download
Headers: Authorization: Bearer <token>

# Download all clips (ZIP)
GET /api/clips/video/<video_id>/download-all
Headers: Authorization: Bearer <token>
```

Full API documentation: http://localhost/docs

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

---

## 📊 Monitoring

### Celery Tasks (Flower)

Access Flower at http://localhost:5555 to monitor:
- Task queue status
- Worker health
- Task history and failures

### Logs

```bash
# View Flask logs
docker-compose -f docker/docker-compose.yml logs -f web

# View Celery worker logs
docker-compose -f docker/docker-compose.yml logs -f celery_worker

# View all logs
docker-compose -f docker/docker-compose.yml logs -f
```

### Health Check

```bash
GET /health
# Returns: { "status": "healthy", "database": "connected" }
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Generate strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure production database (PostgreSQL)
- [ ] Setup S3 for file storage
- [ ] Configure Stripe webhooks
- [ ] Setup Sentry for error tracking
- [ ] Enable HTTPS (SSL certificate)
- [ ] Configure firewall rules
- [ ] Setup automated backups
- [ ] Configure Celery with proper concurrency
- [ ] Setup monitoring (Prometheus/Grafana)

### Deployment Options

**AWS (Recommended):**
- EC2/ECS for application
- RDS for PostgreSQL
- ElastiCache for Redis
- S3 for file storage
- CloudFront for CDN

**Heroku:**
```bash
heroku create binhocut-prod
heroku addons:create heroku-postgresql:standard-0
heroku addons:create heroku-redis:premium-0
git push heroku main
```

**Digital Ocean:**
- App Platform for web service
- Managed PostgreSQL
- Managed Redis
- Spaces for S3-compatible storage

---

## 🐛 Troubleshooting

### Common Issues

**1. Celery worker not processing tasks**
```bash
# Check Redis connection
redis-cli ping

# Restart celery
docker-compose restart celery_worker
```

**2. Database connection errors**
```bash
# Verify PostgreSQL is running
docker-compose ps db

# Check connection
psql postgresql://postgres:postgres@localhost:5432/binhocut
```

**3. Video upload fails**
```bash
# Check disk space
df -h

# Verify upload folder permissions
chmod 777 uploads done temp
```

**4. FFmpeg errors**
```bash
# Test FFmpeg
ffmpeg -version

# Install missing codecs (Ubuntu/Debian)
sudo apt-get install ffmpeg libavcodec-extra
```

---

## 📈 Performance Tips

1. **Enable GPU for Whisper** - Set `USE_GPU=true` if CUDA available
2. **Increase Celery workers** - Adjust `--concurrency` based on CPU cores
3. **Use S3 for storage** - Local disk doesn't scale
4. **Enable Redis caching** - Cache transcription results
5. **Optimize video encoding** - Use `preset=faster` for quicker processing
6. **Database indexing** - Ensure indexes on foreign keys and frequently queried fields

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 💰 Commercial Use

This software is ready for commercial deployment. For enterprise support and custom features:

- 📧 Email: support@binhocut.com
- 🌐 Website: https://binhocut.com
- 📱 WhatsApp: +55 81 9XXXX-XXXX

---

## 🙏 Acknowledgments

- OpenAI Whisper for transcription
- MoviePy for video processing
- MediaPipe for face detection
- Flask ecosystem

---

**Built with ❤️ in Recife, Brazil** 🇧🇷