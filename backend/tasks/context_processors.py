from .colors import person_color
from .models import Notification, Person, Task


def nav_context(request):
    people = list(Person.objects.select_related("user"))
    nav_people = [
        {
            "person": person,
            "count": person.tasks_assigned.count(),
            "color": person_color(i),
        }
        for i, person in enumerate(people)
    ]

    current_person = None
    unread_notifications_count = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        current_person = getattr(user, "person", None)
        if current_person:
            unread_notifications_count = Notification.objects.filter(
                recipient=current_person, read=False
            ).count()

    return {
        "nav_people": nav_people,
        "nav_total_tasks": Task.objects.count(),
        "current_person": current_person,
        "unread_notifications_count": unread_notifications_count,
    }
