from django.urls import path
from .views import (index,add_students,student_edit,process_payment,
                    levelBillView,addlevelbill,editlevelbill,paymentView,search_student,session_add_view,
                    session_update_view,session_delete_view,session_view,summary_links,
                    level_summary,session_summary,session_summary_pdf,import_excel)



app_name = "finance"
urlpatterns = [
    path('import-data', import_excel, name='import'),
    path('balance-summary/', summary_links, name='summary_links'),
    path('balance-summary/<str:level>/', level_summary, name='level_summary'),
    path('balance-summary/<str:level>/<int:session_id>/', session_summary, name='session_summary'),
    path('session_summary_pdf/<str:level>/<int:session_id>/', session_summary_pdf, name='session_summary_pdf'),
    path("", index, name="student"),
    path("view_session", session_view, name="session"),
    path("session_add", session_add_view , name="session_add"),
    path("session_update/<int:pk>", session_update_view , name="session_update"),
    path("session_delete/<int:pk>", session_delete_view , name="session_delete"),
    path("search-student", search_student, name="search_student"),
    path("payment", paymentView, name="paymentsum"),
    path("billing", levelBillView, name="bill"),
    path("add_billing", addlevelbill, name="add_bill"),
    path("add_students",add_students,name="add_student"),
    path('edit-bill/<int:level_id>/', editlevelbill, name='edit_bill'),

    path("edit_students/<str:name>",student_edit,name="edit_student"),
    path('process_payment/<int:student_id>/', process_payment, name='process_payment'),
]
