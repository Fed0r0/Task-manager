import json
import math

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .charts import bar_rows, donut_segments
from .colors import person_color
from .forms import (
    ChecklistItemForm,
    CommentForm,
    PersonCreateForm,
    PersonEditForm,
    ProfileForm,
    ReplyForm,
    TaskForm,
)
from .mentions import mention_targets, resolve_mention_recipients
from .models import Attachment, ChecklistItem, Comment, HistoryEntry, Notification, Person, Task

RING_RADIUS = 46
RING_CIRCUMFERENCE = 2 * math.pi * RING_RADIUS


def _is_admin(user):
    return user.is_authenticated and hasattr(user, "person") and user.person.role == "admin"


def _current_person(request):
    return getattr(request.user, "person", None)


def _log_history(task, person, action):
    HistoryEntry.objects.create(task=task, user=person, action=action)


def _safe_next(request, default="task_list"):
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(candidate, allowed_hosts={request.get_host()}):
        return candidate
    return reverse(default)


def _hx_redirect(url):
    """Redirect a form submitted via htmx: htmx follows this with a real
    browser navigation, instead of swapping the target with a 30x response."""
    response = HttpResponse(status=204)
    response["HX-Redirect"] = url
    return response


@login_required
def dashboard(request):
    tasks = (
        Task.objects.exclude(type="general")
        .select_related("assigned_by")
        .prefetch_related("assigned_to__user", "checklist_items", "active_workers__user")
    )
    total = tasks.count()
    completed = tasks.filter(status="completed").count()
    in_progress = tasks.filter(status="in_progress").count()
    today = timezone.localdate()
    overdue = tasks.filter(deadline__lt=today).exclude(status="completed").count()
    completion_pct = round(completed / total * 100) if total else 0

    people_stats = []
    for i, person in enumerate(Person.objects.select_related("user")):
        assigned = person.tasks_assigned.all()
        count = assigned.count()
        people_stats.append(
            {
                "person": person,
                "count": count,
                "color": person_color(i),
                "status_counts": [
                    ("Not Started", assigned.filter(status="not_started").count(), "var(--st-notstarted)"),
                    ("In Progress", assigned.filter(status="in_progress").count(), "var(--st-progress)"),
                    ("Completed", assigned.filter(status="completed").count(), "var(--st-completed)"),
                ],
                "priority_counts": [
                    ("High", assigned.filter(priority="high").count(), "var(--pri-high)"),
                    ("Medium", assigned.filter(priority="medium").count(), "var(--pri-medium)"),
                    ("Low", assigned.filter(priority="low").count(), "var(--pri-low)"),
                ],
            }
        )

    due_soon = (
        tasks.exclude(status="completed")
        .exclude(deadline__isnull=True)
        .order_by("deadline")[:4]
    )

    return render(
        request,
        "tasks/dashboard.html",
        {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "overdue": overdue,
            "completion_pct": completion_pct,
            "ring_circumference": RING_CIRCUMFERENCE,
            "ring_offset": RING_CIRCUMFERENCE - (completion_pct / 100) * RING_CIRCUMFERENCE,
            "people_stats": people_stats,
            "due_soon": due_soon,
        },
    )


@login_required
def task_list(request):
    tasks_qs = (
        Task.objects.select_related("assigned_by")
        .prefetch_related("assigned_to__user", "checklist_items", "active_workers__user")
    )

    status = request.GET.get("status", "")
    priority = request.GET.get("priority", "")
    task_type = request.GET.get("type", "")
    person_id = request.GET.get("person", "")
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "deadline")

    if status:
        tasks_qs = tasks_qs.filter(status=status)
    if priority:
        tasks_qs = tasks_qs.filter(priority=priority)
    if task_type:
        tasks_qs = tasks_qs.filter(type=task_type)
    if person_id and person_id.isdigit():
        tasks_qs = tasks_qs.filter(assigned_to__id=person_id)
    if query:
        tasks_qs = tasks_qs.filter(title__icontains=query)

    tasks_list = list(tasks_qs.distinct())

    if sort == "priority":
        order = {"high": 0, "medium": 1, "low": 2}
        tasks_list.sort(key=lambda t: order.get(t.priority, 1))
    elif sort == "progress":
        tasks_list.sort(key=lambda t: t.progress, reverse=True)
    else:
        tasks_list.sort(key=lambda t: (t.deadline is None, t.deadline))

    specific_tasks = [t for t in tasks_list if t.type != "general"]
    general_tasks = [t for t in tasks_list if t.type == "general"]

    context = {
        "specific_tasks": specific_tasks,
        "general_tasks": general_tasks,
        "status": status,
        "priority": priority,
        "type": task_type,
        "person": person_id,
        "query": query,
        "sort": sort,
        "status_choices": Task.STATUS_CHOICES,
        "priority_choices": Task.PRIORITY_CHOICES,
        "type_choices": Task.TYPE_CHOICES,
        "selected_person": Person.objects.filter(id=person_id).first() if person_id.isdigit() else None,
    }

    template = "tasks/_task_table.html" if request.headers.get("HX-Request") else "tasks/task_list.html"
    return render(request, template, context)


@login_required
def statistics(request):
    tasks = Task.objects.prefetch_related("checklist_items")
    total = tasks.count()
    completed = tasks.filter(status="completed").count()
    in_progress = tasks.filter(status="in_progress").count()
    today = timezone.localdate()
    overdue = tasks.filter(deadline__lt=today).exclude(status="completed").count()
    avg_progress = round(sum(t.progress for t in tasks) / total) if total else 0

    status_segments = donut_segments(
        [
            ("Not Started", tasks.filter(status="not_started").count(), "var(--st-notstarted)"),
            ("In Progress", tasks.filter(status="in_progress").count(), "var(--st-progress)"),
            ("Completed", tasks.filter(status="completed").count(), "var(--st-completed)"),
        ]
    )
    priority_segments = donut_segments(
        [
            ("High", tasks.filter(priority="high").count(), "var(--pri-high)"),
            ("Medium", tasks.filter(priority="medium").count(), "var(--pri-medium)"),
            ("Low", tasks.filter(priority="low").count(), "var(--pri-low)"),
        ]
    )

    people = list(Person.objects.select_related("user"))
    workload_rows = bar_rows(
        [(str(p), p.tasks_assigned.count(), person_color(i)) for i, p in enumerate(people)]
    )
    workload_rows.sort(key=lambda r: r["value"], reverse=True)

    progress_raw = []
    for i, p in enumerate(people):
        assigned = list(p.tasks_assigned.all())
        avg = round(sum(t.progress for t in assigned) / len(assigned)) if assigned else 0
        progress_raw.append((str(p), avg, person_color(i)))
    progress_rows = bar_rows(progress_raw, relative=False)
    progress_rows.sort(key=lambda r: r["value"], reverse=True)

    return render(
        request,
        "tasks/statistics.html",
        {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "overdue": overdue,
            "avg_progress": avg_progress,
            "status_segments": status_segments,
            "priority_segments": priority_segments,
            "workload_rows": workload_rows,
            "progress_rows": progress_rows,
        },
    )


@login_required
def audit_log(request):
    if not _is_admin(request.user):
        raise PermissionDenied("Only admins can view the audit log.")

    entries = HistoryEntry.objects.select_related("user__user", "task").order_by("-at")
    return render(request, "tasks/audit_log.html", {"entries": entries})


@login_required
def add_person(request):
    if not _is_admin(request.user):
        raise PermissionDenied("Only admins can add team members.")

    if request.method == "POST":
        form = PersonCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("task_list")
    else:
        form = PersonCreateForm()

    return render(request, "tasks/add_person.html", {"form": form})


@login_required
def profile(request):
    next_url = request.POST.get("next") or request.GET.get("next") or "/"

    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            form.save(request.user)
            return _hx_redirect(_safe_next(request))
    else:
        form = ProfileForm(initial={"full_name": request.user.get_full_name()})

    return render(request, "tasks/_profile_modal.html", {"form": form, "next": next_url})


@login_required
def person_edit(request, person_id):
    if not _is_admin(request.user):
        raise PermissionDenied("Only admins can manage team members.")

    person = get_object_or_404(Person, pk=person_id)
    next_url = request.POST.get("next") or request.GET.get("next") or "/"

    if request.method == "POST":
        form = PersonEditForm(request.POST)
        if form.is_valid():
            form.save(person)
            return _hx_redirect(_safe_next(request))
    else:
        form = PersonEditForm(initial={"full_name": str(person)})

    people_ids = list(Person.objects.order_by("id").values_list("id", flat=True))
    avatar_color = person_color(people_ids.index(person.id)) if person.id in people_ids else person_color(0)

    return render(
        request,
        "tasks/_person_edit_modal.html",
        {"person": person, "form": form, "next": next_url, "avatar_color": avatar_color},
    )


@login_required
def person_remove(request, person_id):
    if not _is_admin(request.user):
        raise PermissionDenied("Only admins can manage team members.")

    person = get_object_or_404(Person, pk=person_id)
    next_url = request.POST.get("next") or request.GET.get("next") or "/"
    is_last_admin = person.role == "admin" and Person.objects.filter(role="admin").count() <= 1

    if request.method == "POST":
        if is_last_admin:
            return render(
                request,
                "tasks/_person_remove_confirm.html",
                {"person": person, "next": next_url, "error": "You can't remove the last admin."},
            )
        person.user.delete()
        return _hx_redirect(_safe_next(request))

    return render(
        request,
        "tasks/_person_remove_confirm.html",
        {"person": person, "next": next_url, "error": "You can't remove the last admin." if is_last_admin else ""},
    )


def _render_task_modal(request, task, form, next_url, initial_tab="details"):
    people = Person.objects.select_related("user")
    is_admin = _is_admin(request.user)

    history_entries = None
    if task is not None:
        history_entries = task.history.select_related("user__user")
        if not is_admin:
            history_entries = history_entries.exclude(action__icontains="internal note")

    return render(
        request,
        "tasks/_task_modal.html",
        {
            "form": form,
            "task": task,
            "checklist_form": ChecklistItemForm(),
            "comment_form": CommentForm(),
            "is_admin": is_admin,
            "next": next_url,
            "initial_tab": initial_tab,
            "mention_names_json": json.dumps(mention_targets(people)),
            "history_entries": history_entries,
        },
    )


@login_required
def task_modal(request, task_id=None):
    task = get_object_or_404(Task, pk=task_id) if task_id else None
    next_url = request.POST.get("next") or request.GET.get("next") or "/"

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            creating = task is None
            obj = form.save(commit=False)
            if creating:
                obj.assigned_by = _current_person(request)
            obj.save()
            form.save_m2m()
            _log_history(obj, _current_person(request), "created this task" if creating else "updated task details")
            return _hx_redirect(_safe_next(request))
    else:
        form = TaskForm(instance=task)

    initial_tab = request.GET.get("open_tab", "details")
    return _render_task_modal(request, task, form, next_url, initial_tab)


@login_required
def notifications_panel(request):
    person = _current_person(request)
    notifications = (
        Notification.objects.filter(recipient=person)
        .select_related("comment", "comment__task", "comment__author__user")
        .order_by("-created_at")[:20]
    )
    return render(request, "tasks/_notifications_panel.html", {"notifications": notifications})


@login_required
def notification_open(request, notification_id):
    person = _current_person(request)
    notification = get_object_or_404(Notification, pk=notification_id, recipient=person)
    if not notification.read:
        notification.read = True
        notification.save(update_fields=["read"])

    task = notification.comment.task
    next_url = request.GET.get("next") or "/"
    form = TaskForm(instance=task)
    return _render_task_modal(request, task, form, next_url, initial_tab="activity")


@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    next_url = request.POST.get("next") or request.GET.get("next") or "/"

    if request.method == "POST":
        task.delete()
        return _hx_redirect(_safe_next(request))

    return render(request, "tasks/_task_delete_confirm.html", {"task": task, "next": next_url})


@login_required
def toggle_working(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    person = _current_person(request)

    if request.method == "POST" and person:
        if task.active_workers.filter(pk=person.pk).exists():
            task.active_workers.remove(person)
            _log_history(task, person, "stopped working on this task")
        else:
            task.active_workers.add(person)
            _log_history(task, person, "started working on this task")

    next_url = request.POST.get("next") or request.GET.get("next") or "/"
    return render(request, "tasks/_task_card.html", {"t": task, "next": next_url})


def _checklist_panel_response(request, task):
    return render(
        request,
        "tasks/_modal_checklist_panel.html",
        {"task": task, "checklist_form": ChecklistItemForm()},
    )


@login_required
def checklist_add(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == "POST":
        form = ChecklistItemForm(request.POST)
        if form.is_valid() and form.cleaned_data["text"].strip():
            order = task.checklist_items.count()
            item = ChecklistItem.objects.create(task=task, text=form.cleaned_data["text"].strip(), order=order)
            _log_history(task, _current_person(request), f'added checklist item "{item.text}"')
    return _checklist_panel_response(request, task)


@login_required
def checklist_toggle(request, task_id, item_id):
    task = get_object_or_404(Task, pk=task_id)
    item = get_object_or_404(ChecklistItem, pk=item_id, task=task)
    if request.method == "POST":
        item.done = not item.done
        item.save()
        verb = "checked" if item.done else "unchecked"
        _log_history(task, _current_person(request), f'{verb} checklist item "{item.text}"')
    return _checklist_panel_response(request, task)


@login_required
def checklist_delete(request, task_id, item_id):
    task = get_object_or_404(Task, pk=task_id)
    item = get_object_or_404(ChecklistItem, pk=item_id, task=task)
    if request.method == "POST":
        text = item.text
        item.delete()
        _log_history(task, _current_person(request), f'removed checklist item "{text}"')
    return _checklist_panel_response(request, task)


@login_required
def attachment_add(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == "POST":
        person = _current_person(request)
        for uploaded_file in request.FILES.getlist("file"):
            attachment = Attachment.objects.create(task=task, file=uploaded_file, added_by=person)
            _log_history(task, person, f'attached file "{attachment.filename}"')
    return render(request, "tasks/_modal_attachments_panel.html", {"task": task})


@login_required
def attachment_delete(request, task_id, attachment_id):
    task = get_object_or_404(Task, pk=task_id)
    attachment = get_object_or_404(Attachment, pk=attachment_id, task=task)
    if request.method == "POST":
        name = attachment.filename
        attachment.delete()
        _log_history(task, _current_person(request), f'removed attachment "{name}"')
    return render(request, "tasks/_modal_attachments_panel.html", {"task": task})


def _notify_mentions(comment, author):
    people = list(Person.objects.select_related("user"))
    recipients = resolve_mention_recipients(comment.text, people, exclude=author)
    Notification.objects.bulk_create(Notification(recipient=r, comment=comment) for r in recipients)


def _render_activity_panel(request, task, is_admin):
    people = Person.objects.select_related("user")
    return render(
        request,
        "tasks/_modal_activity_panel.html",
        {
            "task": task,
            "comment_form": CommentForm(),
            "is_admin": is_admin,
            "mention_names_json": json.dumps(mention_targets(people)),
        },
    )


@login_required
def comment_add(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    is_admin = _is_admin(request.user)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid() and form.cleaned_data["text"].strip():
            person = _current_person(request)
            comment = form.save(commit=False)
            comment.task = task
            comment.author = person
            comment.internal = is_admin and comment.internal
            comment.save()
            _log_history(task, person, "added an internal note" if comment.internal else "posted a comment")
            _notify_mentions(comment, person)
    return _render_activity_panel(request, task, is_admin)


@login_required
def comment_reply_add(request, task_id, comment_id):
    task = get_object_or_404(Task, pk=task_id)
    parent = get_object_or_404(Comment, pk=comment_id, task=task, parent__isnull=True)
    is_admin = _is_admin(request.user)
    if request.method == "POST":
        form = ReplyForm(request.POST)
        if form.is_valid() and form.cleaned_data["text"].strip():
            person = _current_person(request)
            reply = form.save(commit=False)
            reply.task = task
            reply.parent = parent
            reply.author = person
            reply.save()
            _log_history(task, person, "replied to a comment")
            _notify_mentions(reply, person)
    return _render_activity_panel(request, task, is_admin)
