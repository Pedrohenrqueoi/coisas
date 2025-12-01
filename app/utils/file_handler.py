# -*- coding: utf-8 -*-
"""
File Handler Utilities
"""
import os
import uuid
from pathlib import Path
from flask import current_app
import boto3
from botocore.exceptions import ClientError


def generate_unique_filename(original_filename, user_id):
    """Generate unique filename with user_id prefix"""
    ext = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())
    return f"user_{user_id}_{unique_id}{ext}"


def save_uploaded_file(file, user_id, folder='upload'):
    """
    Save uploaded file to local storage or S3
    Returns: (file_path, s3_key) or (file_path, None)
    """
    unique_filename = generate_unique_filename(file.filename, user_id)
    
    # Check if S3 is enabled
    if current_app.config.get('USE_S3'):
        s3_key = upload_to_s3(file, unique_filename, folder)
        return None, s3_key
    else:
        # Save locally
        upload_folder = Path(current_app.config['UPLOAD_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_folder / unique_filename
        file.save(str(file_path))
        
        return str(file_path), None


def upload_to_s3(file, filename, folder='upload'):
    """
    Upload file to S3
    Returns: S3 key
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )
    
    bucket_name = current_app.config['AWS_BUCKET_NAME']
    s3_key = f"{folder}/{filename}"
    
    try:
        s3_client.upload_fileobj(
            file,
            bucket_name,
            s3_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        return s3_key
    except ClientError as e:
        raise Exception(f"S3 upload failed: {str(e)}")


def download_from_s3(s3_key, local_path):
    """Download file from S3 to local path"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )
    
    bucket_name = current_app.config['AWS_BUCKET_NAME']
    
    try:
        s3_client.download_file(bucket_name, s3_key, str(local_path))
        return True
    except ClientError as e:
        raise Exception(f"S3 download failed: {str(e)}")


def generate_s3_presigned_url(s3_key, expiration=3600):
    """Generate presigned URL for S3 object"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )
    
    bucket_name = current_app.config['AWS_BUCKET_NAME']
    
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        raise Exception(f"Failed to generate presigned URL: {str(e)}")


def delete_file(file_path=None, s3_key=None):
    """Delete file from local storage or S3"""
    if s3_key:
        # Delete from S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_REGION']
        )
        
        bucket_name = current_app.config['AWS_BUCKET_NAME']
        
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
    
    elif file_path and Path(file_path).exists():
        # Delete from local storage
        try:
            Path(file_path).unlink()
            return True
        except Exception:
            return False
    
    return False


def get_file_size_mb(file_path):
    """Get file size in MB"""
    if Path(file_path).exists():
        size_bytes = Path(file_path).stat().st_size
        return round(size_bytes / (1024 * 1024), 2)
    return 0


def cleanup_old_files(folder, days=7):
    """
    Delete files older than specified days
    Used for scheduled cleanup tasks
    """
    import time
    from datetime import timedelta
    
    folder_path = Path(folder)
    if not folder_path.exists():
        return 0
    
    cutoff_time = time.time() - (days * 86400)
    deleted_count = 0
    
    for file_path in folder_path.iterdir():
        if file_path.is_file():
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception:
                    pass
    
    return deleted_count