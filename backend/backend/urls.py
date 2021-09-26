from django.urls import path
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth.views import LogoutView

from support.views import chat, dashboard, login, queue, settings, staff, statistics, users, lines, install
from support.views.api import chats as api_chats, users as api_users, staff as api_staff, settings as api_settings, \
     queue as api_queue, lines as api_lines, files as api_files, update as api_update
from backend import settings as app_settings

urlpatterns = [
    path('', dashboard.DashboardView.as_view()),
    path('login/', login.CustomLoginView.as_view()),
    path('login', RedirectView.as_view(url='/login/')),
    path('logout/', LogoutView.as_view()),
    path('logout', RedirectView.as_view(url='/logout/')),
    path('chat/', chat.ChatView.as_view()),
    path('chat/<int:chat_id>', chat.ChatView.as_view()),
    path('queue/', queue.QueueView.as_view()),
    path('queue/<int:queue_line>', queue.QueueView.as_view()),
    path('queue/<int:queue_line>/page/<int:page>', queue.QueueView.as_view()),
    path('lines/', lines.LinesView.as_view()),
    path('lines/page/<int:page>', lines.LinesView.as_view()),
    path('settings/', settings.SettingsView.as_view()),
    path('settings/page/<int:page>', settings.SettingsView.as_view()),
    path('statistics/', statistics.StatisticsView.as_view()),
    path('staff/', staff.StaffView.as_view()),
    path('staff/page/<int:page>', staff.StaffView.as_view()),
    path('staff/<int:user_id>', staff.StaffView.as_view()),
    path('users/', users.UsersView.as_view()),
    path('users/page/<int:page>', users.UsersView.as_view()),
    path('users/<int:user_id>', users.UsersView.as_view()),
    path('install/', install.InstallView.as_view()),
    # API endpoints
    path('api/update', api_update.APIUpdateView.as_view()),
    path('api/chats/list', api_chats.APIChatsListView.as_view()),
    path('api/chats/<int:chat_id>/info', api_chats.APIChatsInfoView.as_view()),
    path('api/chats/<int:chat_id>/assignment', api_chats.APIChatsAssignmentView.as_view()),
    path('api/chats/<int:chat_id>/messages', api_chats.APIChatsMessagesView.as_view()),
    path('api/chats/<int:chat_id>/messages/', api_chats.APIChatsMessagesView.as_view()),
    path('api/chats/<int:chat_id>/messages/after/', api_chats.APIChatsMessagesAfterView.as_view()),
    path('api/chats/<int:chat_id>/messages/after/<int:last_message>', api_chats.APIChatsMessagesAfterView.as_view()),
    path('api/chats/<int:chat_id>/messages/before/', api_chats.APIChatsMessagesBeforeView.as_view()),
    path('api/chats/<int:chat_id>/messages/before/<int:first_message>', api_chats.APIChatsMessagesBeforeView.as_view()),
    path('api/chats/<int:chat_id>/queue', api_chats.APIChatsQueueView.as_view()),
    path('api/chats/<int:chat_id>/status', api_chats.APIChatsStatusView.as_view()),
    path('api/users/<int:user_id>/info', api_users.APIUsersInfoView.as_view()),
    path('api/users/<int:user_id>/extra', api_users.APIUsersExtraView.as_view()),
    path('api/users/<int:user_id>/comments', api_users.APIUsersCommentsView.as_view()),
    path('api/users/<int:user_id>/block', api_users.APIUsersBlockView.as_view()),
    path('api/users/finder', api_users.APIUsersFinderView.as_view()),
    path('api/staff/meta', api_staff.APIStaffMetaView.as_view()),
    path('api/staff/list', api_staff.APIStaffListView.as_view()),
    path('api/staff/<int:user_id>/info', api_staff.APIStaffInfoView.as_view()),
    path('api/staff/<int:user_id>/password', api_staff.APIStaffPasswordView.as_view()),
    path('api/staff/<int:user_id>/block', api_staff.APIStaffBlockView.as_view()),
    path('api/settings/list', api_settings.APISettingsListView.as_view()),
    path('api/settings/<int:setting_id>', api_settings.APISettingsInfoView.as_view()),
    path('api/queue/list', api_queue.APIQueueListView.as_view()),
    path('api/queue/assign', api_queue.APIQueueAssignView.as_view()),
    path('api/lines/list', api_lines.APILinesListView.as_view()),
    path('api/lines/<int:line_id>', api_lines.APILinesInfoView.as_view()),
    path('api/files/', api_files.APIFilesView.as_view()),
]

if app_settings.DEBUG:
    urlpatterns += static(app_settings.STATIC_URL, document_root=app_settings.STATIC_DIR)
