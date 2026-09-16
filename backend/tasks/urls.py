from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("tasks/", views.task_list, name="task_list"),
    path("stats/", views.statistics, name="statistics"),
    path("audit/", views.audit_log, name="audit_log"),
    path("people/add/", views.add_person, name="add_person"),
    path("profile/", views.profile, name="profile"),
    path("people/<int:person_id>/edit/", views.person_edit, name="person_edit"),
    path("people/<int:person_id>/remove/", views.person_remove, name="person_remove"),
    path("tasks/new/", views.task_modal, name="task_new"),
    path("tasks/<int:task_id>/edit/", views.task_modal, name="task_edit"),
    path("tasks/<int:task_id>/delete/", views.task_delete, name="task_delete"),
    path("tasks/<int:task_id>/toggle-working/", views.toggle_working, name="toggle_working"),
    path("tasks/<int:task_id>/checklist/add/", views.checklist_add, name="checklist_add"),
    path("tasks/<int:task_id>/checklist/<int:item_id>/toggle/", views.checklist_toggle, name="checklist_toggle"),
    path("tasks/<int:task_id>/checklist/<int:item_id>/delete/", views.checklist_delete, name="checklist_delete"),
    path("tasks/<int:task_id>/attachments/add/", views.attachment_add, name="attachment_add"),
    path(
        "tasks/<int:task_id>/attachments/<int:attachment_id>/delete/",
        views.attachment_delete,
        name="attachment_delete",
    ),
    path("tasks/<int:task_id>/comments/add/", views.comment_add, name="comment_add"),
    path("tasks/<int:task_id>/comments/<int:comment_id>/reply/", views.comment_reply_add, name="comment_reply_add"),
    path("notifications/", views.notifications_panel, name="notifications_panel"),
    path("notifications/<int:notification_id>/open/", views.notification_open, name="notification_open"),
]
