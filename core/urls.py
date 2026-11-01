from django.urls import path
from .handlers import assessments, academics, attendance, certificates, class_transfers, dashboard, grades, students, system, tuition

urlpatterns = [
    # Trang chủ
    path('', dashboard.home, name='home'),

    # Quản lý học viên
    path('students/', students.student_list, name='student_list'),
    path('students/export/excel/', students.student_export_excel, name='student_export_excel'),
    path('students/add/', students.student_add, name='student_add'),
    path(
        'students/edit/<int:student_id>/',
        students.student_edit,
        name='student_edit'
    ),
    path(
        'students/delete/<int:student_id>/',
        students.student_delete,
        name='student_delete'
    ),

    # Quản lý khóa học
    path('courses/', academics.course_list, name='course_list'),
    path('courses/add/', academics.course_add, name='course_add'),
    path(
        'courses/edit/<int:course_id>/',
        academics.course_edit,
        name='course_edit'
    ),
    path(
        'courses/delete/<int:course_id>/',
        academics.course_delete,
        name='course_delete'
    ),

    # Quản lý lớp học
    path('classes/', academics.class_list, name='class_list'),
    path('classes/add/', academics.class_add, name='class_add'),
    path(
        'classes/edit/<int:class_id>/',
        academics.class_edit,
        name='class_edit'
    ),
    path(
        'classes/<int:class_id>/',
        academics.class_detail,
        name='class_detail'
    ),
    path(
        'classes/<int:class_id>/students/<int:student_id>/remove/',
        academics.student_remove_from_class,
        name='student_remove_from_class'
    ),
    path(
        'classes/<int:class_id>/students/<int:student_id>/status/',
        academics.enrollment_status_update,
        name='enrollment_status_update'
    ),
    path(
        'classes/<int:class_id>/students/<int:student_id>/transfer/',
        academics.enrollment_transfer,
        name='enrollment_transfer'
    ),
    path(
        'class-transfers/',
        class_transfers.class_transfer_list,
        name='class_transfer_list',
    ),
    path(
        'class-transfers/<int:transfer_id>/approve/',
        class_transfers.class_transfer_approve,
        name='class_transfer_approve',
    ),
    path(
        'class-transfers/<int:transfer_id>/reject/',
        class_transfers.class_transfer_reject,
        name='class_transfer_reject',
    ),

    # Quản lý buổi học và điểm danh
    path(
        'classes/<int:class_id>/sessions/',
        attendance.session_list,
        name='session_list',
    ),
    path(
        'classes/<int:class_id>/sessions/add/',
        attendance.session_add,
        name='session_add',
    ),
    path(
        'classes/sessions/<int:session_id>/attendance/',
        attendance.session_attendance,
        name='session_attendance',
    ),
    path(
        'classes/<int:class_id>/attendance/report/',
        attendance.class_attendance_report,
        name='class_attendance_report',
    ),
    path(
        'assessment-policies/',
        assessments.assessment_policy_list,
        name='assessment_policy_list',
    ),
    path(
        'assessment-policies/add/',
        assessments.assessment_policy_create,
        name='assessment_policy_create',
    ),
    path(
        'assessment-policies/<int:policy_id>/activate/',
        assessments.assessment_policy_activate,
        name='assessment_policy_activate',
    ),
    path(
        'assessment-policies/<int:policy_id>/archive/',
        assessments.assessment_policy_archive,
        name='assessment_policy_archive',
    ),
    path(
        'assessments/classes/',
        assessments.assessment_class_list,
        name='assessment_class_list',
    ),
    path(
        'classes/<int:class_id>/assessments/',
        assessments.class_assessments,
        name='class_assessments',
    ),
    path(
        'classes/<int:class_id>/assessments/add/',
        assessments.assessment_event_create,
        name='assessment_event_create',
    ),
    path(
        'assessment-events/<int:event_id>/',
        assessments.assessment_event_gradebook,
        name='assessment_event_gradebook',
    ),

    # Quản lý giáo viên
    path('teachers/', academics.teacher_list, name='teacher_list'),
    path('teachers/add/', academics.teacher_add, name='teacher_add'),
    path(
        'teachers/edit/<int:teacher_id>/',
        academics.teacher_edit,
        name='teacher_edit'
    ),
    path(
        'teachers/delete/<int:teacher_id>/',
        academics.teacher_delete,
        name='teacher_delete'
    ),

    # Quản lý điểm số
    path('grades/', grades.grade_list, name='grade_list'),
    path('grades/add/', grades.grade_add, name='grade_add'),
    path(
        'grades/edit/<int:grade_id>/',
        grades.grade_edit,
        name='grade_edit'
    ),
    path(
        'grades/delete/<int:grade_id>/',
        grades.grade_delete,
        name='grade_delete'
    ),

    # Quản lý học phí
    path('tuitions/', tuition.tuition_list, name='tuition_list'),
    path('tuitions/export/excel/', tuition.tuition_export_excel, name='tuition_export_excel'),
    path('tuitions/add/', tuition.tuition_add, name='tuition_add'),
    path(
        'tuitions/<int:tuition_id>/receipt/',
        tuition.tuition_receipt,
        name='tuition_receipt',
    ),
    path(
        'tuitions/<int:tuition_id>/pay/',
        tuition.tuition_payment_add,
        name='tuition_payment_add',
    ),
    path(
        'tuitions/edit/<int:tuition_id>/',
        tuition.tuition_edit,
        name='tuition_edit'
    ),
    path(
        'tuitions/delete/<int:tuition_id>/',
        tuition.tuition_delete,
        name='tuition_delete'
    ),
    path('certificates/', certificates.certificate_list, name='certificate_list'),
    path('certificates/add/', certificates.certificate_add, name='certificate_add'),
    path(
        'certificates/<int:certificate_id>/issue/',
        certificates.certificate_issue,
        name='certificate_issue',
    ),
    path('certificates/verify/', certificates.certificate_verify, name='certificate_verify'),

    # Quản trị hệ thống (Tài khoản & Phân quyền)
    path('system/users/', system.user_list, name='user_list'),
    path('system/users/add/', system.user_add, name='user_add'),
    path('system/users/<int:user_id>/edit/', system.user_edit, name='user_edit'),
    path('system/users/<int:user_id>/toggle-status/', system.user_toggle_status, name='user_toggle_status'),
    path('system/users/<int:user_id>/delete/', system.user_delete, name='user_delete'),
    path('system/roles/', system.role_list, name='role_list'),
]

