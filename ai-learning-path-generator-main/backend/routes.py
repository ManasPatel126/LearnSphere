"""
API Routes for task management
"""
import os
import uuid
import json
from flask import Blueprint, request, jsonify
from rq import Queue
from datetime import datetime
import redis

api_bp = Blueprint('rq_api', __name__)

# Redis connection
# Note: decode_responses=False is required for RQ (job results are pickled bytes, not strings)
REDIS_URL = os.getenv('REDIS_URL')
if REDIS_URL and REDIS_URL.startswith(('redis://', 'rediss://')):
    if REDIS_URL.startswith('rediss://'):
        # TLS endpoint: allow self-signed certs if provider uses them
        redis_client = redis.from_url(REDIS_URL, decode_responses=False, ssl_cert_reqs=None)
    else:
        # Non-TLS endpoint: do not pass TLS-only kwargs
        redis_client = redis.from_url(REDIS_URL, decode_responses=False)
else:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        decode_responses=False
    )

@api_bp.route('/generate', methods=['POST'])
def generate_path():
    """
    Queue a learning path generation task using RQ.
    Returns the job ID immediately.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['topic', 'expertise_level', 'duration_weeks', 'time_commitment']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Enqueue job on RQ queue
        q = Queue('learning-paths', connection=redis_client)
        job = q.enqueue('worker.tasks.generate_learning_path_for_worker', data)
        
        return jsonify({
            "task_id": job.id,
            "status": "queued",
            "message": "Learning path generation started"
        }), 202
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """
    Get the current status of an RQ job
    """
    try:
        q = Queue('learning-paths', connection=redis_client)
        job = q.fetch_job(task_id)
        if job is None:
            return jsonify({"error": "Task not found"}), 404
        
        resp = {
            "task_id": job.id,
            "status": job.get_status()
        }
        if job.is_finished:
            resp["result"] = job.result
        if job.is_failed:
            resp["error"] = str(job.exc_info)
        return jsonify(resp), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    """
    Get the final result of an RQ job
    """
    try:
        q = Queue('learning-paths', connection=redis_client)
        job = q.fetch_job(task_id)
        if job is None:
            return jsonify({"error": "Task not found"}), 404
        
        if not job.is_finished:
            return jsonify({
                "error": "Task not yet complete",
                "status": job.get_status()
            }), 202
        
        return jsonify(job.result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
