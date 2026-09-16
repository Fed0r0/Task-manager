import os

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Person(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")

    class Meta:
        verbose_name_plural = "People"

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def initial(self):
        name = str(self)
        return name[0].upper() if name else "?"


class Task(models.Model):
    TYPE_CHOICES = [
        ("specific", "Specific"),
        ("general", "General"),
    ]
    PRIORITY_CHOICES = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]
    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="specific")

    assigned_to = models.ManyToManyField(Person, related_name="tasks_assigned", blank=True)
    assigned_by = models.ForeignKey(
        Person, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks_created"
    )
    active_workers = models.ManyToManyField(Person, related_name="active_tasks", blank=True)

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")

    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def progress(self):
        items = self.checklist_items.all()
        if not items:
            return 0
        done = sum(1 for item in items if item.done)
        return round(done / len(items) * 100)

    @property
    def is_overdue(self):
        if self.status == "completed" or not self.deadline:
            return False
        return self.deadline < timezone.localdate()

    @property
    def due_status(self):
        if self.status == "completed":
            return {"key": "completed", "label": "Completed", "color": "var(--clr-completed)"}
        if self.status == "not_started":
            return {"key": "notstarted", "label": "Not Started", "color": "var(--st-notstarted)"}
        if self.type == "general" or not self.deadline:
            return {"key": "inprogress", "label": "Recurring", "color": "var(--clr-inprogress)"}
        today = timezone.localdate()
        if self.deadline < today:
            return {"key": "overdue", "label": "Overdue", "color": "var(--clr-overdue)"}
        if self.deadline == today:
            return {"key": "duetoday", "label": "Due Today", "color": "var(--clr-duetoday)"}
        if (self.deadline - today).days <= 7:
            return {"key": "dueweek", "label": "Due This Week", "color": "var(--clr-dueweek)"}
        return {"key": "inprogress", "label": "In Progress", "color": "var(--clr-inprogress)"}


class ChecklistItem(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="checklist_items")
    text = models.CharField(max_length=255)
    done = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text


class Attachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/%Y/%m/")
    added_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    @property
    def filename(self):
        return os.path.basename(self.file.name)


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    text = models.TextField()
    internal = models.BooleanField(default=False, help_text="Visible to admins only")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author}: {self.text[:40]}"


class Notification(models.Model):
    recipient = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="notifications")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="notifications")
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.recipient} — comment #{self.comment_id}"


class HistoryEntry(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="history")
    user = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-at"]
        verbose_name_plural = "History entries"

    def __str__(self):
        return f"{self.at:%Y-%m-%d %H:%M} — {self.action}"
