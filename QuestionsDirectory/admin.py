from django.contrib import admin
from .models import QuestionDeck, Question, QuestionOption

# Register your models here.


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4  # Default to 4 options (A, B, C, D)
    can_delete_extra = False

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('word', 'difficulty', 'created_at')
    list_filter = ('difficulty', 'created_at')
    search_fields = ('word', 'definition')
    inlines = [QuestionOptionInline]
    ordering = ('-created_at',)

@admin.register(QuestionDeck)
class QuestionDeckAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
