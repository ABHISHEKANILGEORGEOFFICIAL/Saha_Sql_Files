from django.urls import path
from .views import (
    AddReply,
    CreatePost,
    PostDetail,
    PostList,
    ToggleLike,
    TuitionListCreate,
    TuitionDetail,
    TaskDetail,
    TeacherCourseAPI,
    CourseSectionAPI,
    CourseVideoAPI,
    CourseNoteAPI,
    CourseAssignmentAPI,
    CourseAssignmentSubmissionAPI,
    CourseEnrollmentAPI,
    CourseCertificateAPI,
    CourseReviewAPI,
    CourseCommentAPI,
    CoursePaymentAPI,
    CourseReviewReplyAPI,
    StudentCourseCollectionAPI,
    StudentCourseCollectionItemAPI,
)

from .views import (
    StudyRequestDecision,
    StudyRequestIncomingList,
    StudyRequestListCreate,
    StudyRequestOutgoingList,
    PostList,
    CreatePost,
    PostDetail,
    AddReply,
    ToggleLike,
    TuitionListCreate,
    TuitionDetail,
    TuitionTaskList,
    TuitionTaskByType,
    TaskDetail,
    DeletePost,
    ReportPost,
    TeacherLogoutView,
)

urlpatterns = [
    path("logout/", TeacherLogoutView.as_view()),
    # Study requests (future mobile-to-web chat onboarding)
    path("study-requests/", StudyRequestListCreate.as_view()),
    path("study-requests/incoming/", StudyRequestIncomingList.as_view()),
    path("study-requests/outgoing/", StudyRequestOutgoingList.as_view()),
    path("study-requests/<int:request_id>/decision/", StudyRequestDecision.as_view()),
    # Tuition
    path("tuition/", TuitionListCreate.as_view()),
    path("tuition/<int:id>/", TuitionDetail.as_view()),
    # Tasks — scoped to a tuition
    path("tuition/<int:tuition_id>/tasks/", TuitionTaskList.as_view()),
    path(
        "tuition/<int:tuition_id>/tasks/<str:task_type>/", TuitionTaskByType.as_view()
    ),
    # Task detail (get / update / delete by task id)
    path("task/<int:id>/", TaskDetail.as_view()),
    # Posts (teacher wall — standalone posts, community=None)
    path("posts/", PostList.as_view()),
    path("posts/create/", CreatePost.as_view()),
    path("posts/<int:id>/", PostDetail.as_view()),
    path("posts/<int:id>/reply/", AddReply.as_view()),
    path("posts/<int:id>/like/", ToggleLike.as_view()),
    # 🎓 Courses
    path("courses/", TeacherCourseAPI.as_view()),
    path("courses/<int:pk>/", TeacherCourseAPI.as_view()),
    # 📂 Sections
    path("sections/", CourseSectionAPI.as_view()),
    path("sections/<int:pk>/", CourseSectionAPI.as_view()),
    # 🎥 Videos
    path("videos/", CourseVideoAPI.as_view()),
    path("videos/<int:pk>/", CourseVideoAPI.as_view()),
    # 📝 Notes
    path("notes/", CourseNoteAPI.as_view()),
    path("notes/<int:pk>/", CourseNoteAPI.as_view()),
    # 📚 Assignments
    path("assignments/", CourseAssignmentAPI.as_view()),
    path("assignments/<int:pk>/", CourseAssignmentAPI.as_view()),
    # 📤 Submissions
    path("submissions/", CourseAssignmentSubmissionAPI.as_view()),
    path("submissions/<int:pk>/", CourseAssignmentSubmissionAPI.as_view()),
    # 📊 Enrollment
    path("enrollments/", CourseEnrollmentAPI.as_view()),
    path("enrollments/<int:pk>/", CourseEnrollmentAPI.as_view()),
    # 🎓 Certificates
    path("certificates/", CourseCertificateAPI.as_view()),
    path("certificates/<int:pk>/", CourseCertificateAPI.as_view()),
    # ⭐ Reviews
    path("reviews/", CourseReviewAPI.as_view()),
    path("reviews/<int:pk>/", CourseReviewAPI.as_view()),
    path("courses/<int:course_id>/reviews/", CourseReviewAPI.as_view()),
    # 👨‍🏫 Teacher reply to review
    path("reviews/<int:review_id>/reply/", CourseReviewReplyAPI.as_view()),
    # 💬 Comments
    path("comments/", CourseCommentAPI.as_view()),
    path("comments/<int:pk>/", CourseCommentAPI.as_view()),
    path("courses/<int:course_id>/comments/", CourseCommentAPI.as_view()),
    # 💳 Payments
    path("payments/", CoursePaymentAPI.as_view()),
    path("payments/<int:pk>/", CoursePaymentAPI.as_view()),
    # 📁 Student Course Collections
    path("collections/", StudentCourseCollectionAPI.as_view()),
    path("collections/<int:pk>/", StudentCourseCollectionAPI.as_view()),

    # 📌 Collection Items
    path("collections/<int:collection_id>/items/", StudentCourseCollectionItemAPI.as_view()),
    path("collection-items/<int:pk>/", StudentCourseCollectionItemAPI.as_view()),
    path("posts/<int:id>/delete/", DeletePost.as_view()),  # ← add
    path("posts/<int:id>/report/", ReportPost.as_view()),  # ← add
]
