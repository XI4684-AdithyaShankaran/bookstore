"""
GCP Pub/Sub Task Queue System for Bkmrk'd
Replaces Celery with Google Cloud Pub/Sub for better cloud integration
"""
import os
import json
import asyncio
import logging
from typing import Any, Dict, Optional
from google.cloud import pubsub_v1
from google.cloud import tasks_v2
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class GCPTaskQueue:
    """GCP Pub/Sub and Cloud Tasks based task queue"""
    
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID', 'bookstore-project-464717')
        self.location = os.getenv('GCP_LOCATION', 'us-central1')
        
        # Initialize Pub/Sub client
        try:
            self.publisher = pubsub_v1.PublisherClient()
            self.subscriber = pubsub_v1.SubscriberClient()
            logger.info("✅ GCP Pub/Sub client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Pub/Sub client initialization failed: {e}")
            self.publisher = None
            self.subscriber = None
        
        # Initialize Cloud Tasks client
        try:
            self.tasks_client = tasks_v2.CloudTasksClient()
            logger.info("✅ GCP Cloud Tasks client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Cloud Tasks client initialization failed: {e}")
            self.tasks_client = None
    
    def send_task(self, task_name: str, payload: Dict[str, Any], delay: int = 0) -> bool:
        """Send task to appropriate queue"""
        try:
            if delay > 0:
                # Use Cloud Tasks for delayed tasks
                return self._send_delayed_task(task_name, payload, delay)
            else:
                # Use Pub/Sub for immediate tasks
                return self._send_pubsub_task(task_name, payload)
        except Exception as e:
            logger.error(f"❌ Failed to send task {task_name}: {e}")
            return False
    
    def _send_pubsub_task(self, task_name: str, payload: Dict[str, Any]) -> bool:
        """Send task via Pub/Sub"""
        if not self.publisher:
            return False
        
        topic_path = self.publisher.topic_path(self.project_id, f"bookstore-{task_name}")
        message_data = json.dumps(payload).encode('utf-8')
        
        future = self.publisher.publish(topic_path, message_data)
        future.result()  # Wait for publish to complete
        
        logger.info(f"✅ Task {task_name} sent via Pub/Sub")
        return True
    
    def _send_delayed_task(self, task_name: str, payload: Dict[str, Any], delay: int) -> bool:
        """Send delayed task via Cloud Tasks"""
        if not self.tasks_client:
            return False
        
        queue_path = self.tasks_client.queue_path(
            self.project_id, self.location, f"bookstore-{task_name}"
        )
        
        task = {
            'http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'url': f"https://your-backend-url/tasks/{task_name}",
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(payload).encode('utf-8')
            }
        }
        
        if delay > 0:
            import datetime
            from google.protobuf import timestamp_pb2
            
            schedule_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=delay)
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(schedule_time)
            task['schedule_time'] = timestamp
        
        response = self.tasks_client.create_task(parent=queue_path, task=task)
        logger.info(f"✅ Delayed task {task_name} scheduled: {response.name}")
        return True

# Task definitions
class BookstoreTasks:
    """Task definitions for bookstore operations"""
    
    def __init__(self):
        self.queue = GCPTaskQueue()
    
    def process_book_recommendation(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Process book recommendation task"""
        return self.queue.send_task('book-recommendation', {
            'user_id': user_id,
            'preferences': preferences,
            'timestamp': str(datetime.datetime.utcnow())
        })
    
    def update_book_embeddings(self, book_id: int) -> bool:
        """Update book embeddings in Weaviate"""
        return self.queue.send_task('book-embeddings', {
            'book_id': book_id,
            'action': 'update',
            'timestamp': str(datetime.datetime.utcnow())
        })
    
    def send_email_notification(self, user_id: int, email_type: str, data: Dict[str, Any]) -> bool:
        """Send email notification"""
        return self.queue.send_task('email-notification', {
            'user_id': user_id,
            'email_type': email_type,
            'data': data,
            'timestamp': str(datetime.datetime.utcnow())
        })
    
    def process_analytics_data(self, event_data: Dict[str, Any]) -> bool:
        """Process analytics data for BigQuery"""
        return self.queue.send_task('analytics-processing', {
            'event_data': event_data,
            'timestamp': str(datetime.datetime.utcnow())
        })

# Global task queue instance
task_queue = BookstoreTasks() 