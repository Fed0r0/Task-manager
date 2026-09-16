from django import forms
from django.contrib.auth.models import User

from .models import ChecklistItem, Comment, Person, Task


class PersonCreateForm(forms.Form):
    full_name = forms.CharField(label="Full name", max_length=150)
    username = forms.CharField(label="Username", max_length=150)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    role = forms.ChoiceField(label="Role", choices=Person.ROLE_CHOICES)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self):
        full_name = self.cleaned_data["full_name"].strip()
        first_name, _, last_name = full_name.partition(" ")
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            password=self.cleaned_data["password"],
            first_name=first_name,
            last_name=last_name,
        )
        return Person.objects.create(user=user, role=self.cleaned_data["role"])


class ProfileForm(forms.Form):
    full_name = forms.CharField(label="Your name", max_length=150)

    def save(self, user):
        full_name = self.cleaned_data["full_name"].strip()
        first_name, _, last_name = full_name.partition(" ")
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=["first_name", "last_name"])


class PersonEditForm(forms.Form):
    full_name = forms.CharField(label="Full name", max_length=150)

    def save(self, person):
        full_name = self.cleaned_data["full_name"].strip()
        first_name, _, last_name = full_name.partition(" ")
        person.user.first_name = first_name
        person.user.last_name = last_name
        person.user.save(update_fields=["first_name", "last_name"])


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "type",
            "description",
            "assigned_to",
            "priority",
            "status",
            "start_date",
            "deadline",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. Prepare monthly financial report"}),
            "type": forms.RadioSelect,
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "What does this task involve?"}),
            "assigned_to": forms.CheckboxSelectMultiple,
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = Person.objects.select_related("user")
        self.fields["assigned_to"].required = False
        self.fields["start_date"].required = False
        self.fields["deadline"].required = False


class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ["text"]
        widgets = {"text": forms.TextInput(attrs={"placeholder": "Add a checklist item and press Enter"})}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text", "internal"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "Write a comment. Use @Name to mention someone, or @Supervisor / @Admin.",
                }
            )
        }


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        widgets = {"text": forms.Textarea(attrs={"rows": 2, "placeholder": "Write a reply..."})}
