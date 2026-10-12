
from django.urls import path
from . import views

urlpatterns = [
    # Trang chủ
    path('', views.home, name='home'),

    # Quản lý học viên
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path(
        'students/edit/<int:student_id>/',
        views.student_edit,
        name='student_edit'
    ),
    path(
        'students/delete/<int:student_id>/',
        views.student_delete,
        name='student_delete'
    ),

    # Quản lý khóa học
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.course_add, name='course_add'),
    path(
        'courses/edit/<int:course_id>/',
        views.course_edit,
        name='course_edit'
    ),
    path(
        'courses/delete/<int:course_id>/',
        views.course_delete,
        name='course_delete'
    ),

    # Quản lý lớp học
    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.class_add, name='class_add'),
    path(
        'classes/edit/<int:class_id>/',
        views.class_edit,
        name='class_edit'
    ),
    path(
        'classes/<int:class_id>/',
        views.class_detail,
        name='class_detail'
    ),
    path(
        'classes/<int:class_id>/students/<int:student_id>/remove/',
        views.student_remove_from_class,
        name='student_remove_from_class'
    ),

    # Quản lý giáo viên
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.teacher_add, name='teacher_add'),
    path(
        'teachers/edit/<int:teacher_id>/',
        views.teacher_edit,
        name='teacher_edit'
    ),
    path(
        'teachers/delete/<int:teacher_id>/',
        views.teacher_delete,
        name='teacher_delete'
    ),

    # Quản lý điểm số
    path('grades/', views.grade_list, name='grade_list'),
    path('grades/add/', views.grade_add, name='grade_add'),
    path(
        'grades/edit/<int:grade_id>/',
        views.grade_edit,
        name='grade_edit'
    ),
    path(
        'grades/delete/<int:grade_id>/',
        views.grade_delete,
        name='grade_delete'
    ),

    # Quản lý học phí
    path('tuitions/', views.tuition_list, name='tuition_list'),
    path('tuitions/add/', views.tuition_add, name='tuition_add'),
    path(
        'tuitions/edit/<int:tuition_id>/',
        views.tuition_edit,
        name='tuition_edit'
    ),
    path(
        'tuitions/delete/<int:tuition_id>/',
        views.tuition_delete,
        name='tuition_delete'
    ),
    path(
    "certificates/",
    views.certificate_list,
    name="certificate_list",
),
path(
    "certificates/<int:certificate_id>/issue/",
    views.certificate_issue,
    name="certificate_issue",
),
path(
    "certificates/verify/",
    views.certificate_verify,
    name="certificate_verify",
),
]

