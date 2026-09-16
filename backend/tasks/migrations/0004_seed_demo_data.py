from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils import timezone


def seed_demo_data(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Person = apps.get_model("tasks", "Person")
    Task = apps.get_model("tasks", "Task")
    ChecklistItem = apps.get_model("tasks", "ChecklistItem")
    Comment = apps.get_model("tasks", "Comment")
    Notification = apps.get_model("tasks", "Notification")
    HistoryEntry = apps.get_model("tasks", "HistoryEntry")

    # Only ever seed a genuinely empty database — never touch a database
    # that already has real accounts in it.
    if User.objects.exists():
        return

    jordan_user = User.objects.create(
        username="jblake",
        first_name="Jordan",
        last_name="Blake",
        password=make_password("Harbor42Kite"),
        is_staff=True,
        is_superuser=True,
    )
    jordan = Person.objects.create(user=jordan_user, role="admin")

    maya_user = User.objects.create(
        username="mchen",
        first_name="Maya",
        last_name="Chen",
        password=make_password("Violet9Stream"),
    )
    maya = Person.objects.create(user=maya_user, role="member")

    today = timezone.localdate()

    def log(task, person, action):
        HistoryEntry.objects.create(task=task, user=person, action=action)

    # Specific task, in progress, with a partly-checked checklist so the
    # progress bar and "Due this week" badge both have something to show.
    t1 = Task.objects.create(
        title="Prepare Q1 financial report",
        description="Pull the numbers together and format the report for review.",
        type="specific",
        priority="high",
        status="in_progress",
        start_date=today,
        deadline=today + timedelta(days=5),
        assigned_by=jordan,
    )
    t1.assigned_to.add(maya)
    ChecklistItem.objects.create(task=t1, text="Collect department numbers", done=True, order=0)
    ChecklistItem.objects.create(task=t1, text="Draft the summary", done=True, order=1)
    ChecklistItem.objects.create(task=t1, text="Send for review", done=False, order=2)
    log(t1, jordan, "created this task")
    log(t1, maya, 'checked checklist item "Collect department numbers"')
    log(t1, maya, 'checked checklist item "Draft the summary"')

    comment = Comment.objects.create(
        task=t1,
        author=jordan,
        text="@Maya great progress, please finish by Friday.",
    )
    log(t1, jordan, "posted a comment")
    Notification.objects.create(recipient=maya, comment=comment)

    # Overdue task, so the "Overdue" dashboard tile has something to count.
    t2 = Task.objects.create(
        title="Renew office equipment insurance",
        description="Contact the provider and confirm the new policy terms.",
        type="specific",
        priority="high",
        status="not_started",
        start_date=today - timedelta(days=10),
        deadline=today - timedelta(days=2),
        assigned_by=jordan,
    )
    t2.assigned_to.add(jordan)
    log(t2, jordan, "created this task")

    # Completed task, shared between both people.
    t3 = Task.objects.create(
        title="Onboard new office laptop",
        description="Set up accounts and install required software.",
        type="specific",
        priority="medium",
        status="completed",
        start_date=today - timedelta(days=14),
        deadline=today - timedelta(days=7),
        assigned_by=maya,
    )
    t3.assigned_to.set([jordan, maya])
    ChecklistItem.objects.create(task=t3, text="Install software", done=True, order=0)
    log(t3, maya, "created this task")
    log(t3, jordan, 'checked checklist item "Install software"')

    # General/recurring task, no deadline.
    t4 = Task.objects.create(
        title="Weekly team status update",
        description="Post a short update in the team channel every week.",
        type="general",
        priority="low",
        status="in_progress",
        start_date=today,
        assigned_by=jordan,
    )
    t4.assigned_to.add(maya)
    log(t4, jordan, "created this task")


def unseed_demo_data(apps, schema_editor):
    User = apps.get_model("auth", "User")
    User.objects.filter(username__in=["jblake", "mchen"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tasks", "0003_comment_parent_notification"),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, unseed_demo_data),
    ]
