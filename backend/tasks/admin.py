from django.contrib import admin

from .models import Attachment, ChecklistItem, Comment, HistoryEntry, Person, Task


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


class HistoryEntryInline(admin.TabularInline):
    model = HistoryEntry
    extra = 0
    readonly_fields = ["user", "action", "at"]
    can_delete = False


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "type", "status", "priority", "progress", "deadline", "assigned_by"]
    list_filter = ["status", "priority", "type"]
    search_fields = ["title", "description"]
    filter_horizontal = ["assigned_to"]
    inlines = [ChecklistItemInline, AttachmentInline, CommentInline, HistoryEntryInline]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["__str__", "role"]
    list_filter = ["role"]


admin.site.register(HistoryEntry)
