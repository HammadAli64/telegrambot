from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin/pending/", views.pending_page, name="pending_page"),
    path("admin/tasks/", views.tasks_page, name="tasks_page"),
    path("admin/members/", views.members_page, name="members_page"),
    path("api/pending/", views.pending_tasks_api, name="pending_tasks_api"),
    path("api/tasks/", views.all_tasks_api, name="all_tasks_api"),
    path("api/task/<int:task_id>/approve/", views.approve_task_api, name="approve_task_api"),
    path("api/task/<int:task_id>/reject/", views.reject_task_api, name="reject_task_api"),
    path("api/task/<int:task_id>/update/", views.update_task_api, name="update_task_api"),
    path("api/task/<int:task_id>/delete/", views.delete_task_api, name="delete_task_api"),
    path("api/members/", views.members_api, name="members_api"),
    path("api/members/add/", views.add_member_api, name="add_member_api"),
    path("api/members/remove/", views.remove_member_api, name="remove_member_api"),
]
