import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

import traceback

try:
    from app.notification_scheduler import run_scheduled_notifications, enabled_notification_types_for_feed
    from app.models import AdminNotification

    print("Running scheduled notifications...")
    run_scheduled_notifications()
    print("OK")

    print("Getting enabled types...")
    enabled = enabled_notification_types_for_feed()
    print(f"Enabled: {enabled}")

    print("Querying notifications feed...")
    qs = AdminNotification.objects(notification_type__in=list(enabled)).order_by("-created_at")[:5]
    items = [n.to_feed_dict() for n in qs]
    print(f"Got {len(items)} notifications — feed is working correctly")

except Exception as e:
    traceback.print_exc()
