from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator

from support.models import Chats, Lines
from support.extras.locale import get_correct_case_for_number

"""
Queue statuses:
- new: new or reopened chat
- open: client answered on chat
- answered: we are waiting for response from client
- closed: closed by support
"""


class QueueView(View, LoginRequiredMixin):
    def get(self, request, queue_line=None, page=1, page_size=20, *args, **kwargs):
        errors = list()

        staff_user = request.user

        if queue_line is None:
            return redirect(f'/queue/{staff_user.meta.line.id}')

        selected_line = Lines.get(queue_line)
        if selected_line is None:
            errors.append({
                'text': 'Выбранная линия поддержки не существует',
                'description': None,
            })
            selected_line = staff_user.meta.line

        queue = list()
        now = datetime.now()

        pagination = Paginator(Chats.get_opened_chats(line=selected_line), page_size)

        if page > pagination.num_pages or page < 1:
            chats = list()
            errors.append({
                'text': f'Страница #{page} не существует',
                'description': None,
            })
        else:
            chats = pagination.page(page).object_list

        for chat in chats:
            # fuck datetime.timedelta
            corrected_datetime = chat.last_action.replace(tzinfo=now.astimezone().tzinfo).timestamp()
            delta = timedelta(seconds=datetime.now().timestamp() - corrected_datetime)

            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            timer_status = 'ok'
            if minutes >= 30 and hours == 0:
                timer_status = 'warning'
            elif hours >= 1:
                timer_status = 'problem'

            timer_string = ''
            if days > 0:
                correct_case = get_correct_case_for_number(days, ['день', 'дня', 'дней'])
                timer_string += f'{days} {correct_case} '

            if hours > 0:
                correct_case = get_correct_case_for_number(hours, ['час', 'часа', 'часов'])
                timer_string += f'{hours} {correct_case} '

            # TODO fix for 0 minutes (now - empty string)
            if minutes > 0 and days == 0:
                correct_case = get_correct_case_for_number(minutes, ['минута', 'минуты', 'минут'])
                timer_string += f'{minutes} {correct_case} '

            timer_string = timer_string.rstrip()

            queue.append({
                'chat': chat,
                'last_message': chat.get_last_real_message(),
                'timer': timer_string,
                'timer_status': timer_status,
            })

        context = {
            "queue": queue,
            "queue_line": queue_line,
            "pagination": {
                "page": page,
                "pages_count": pagination.num_pages,
                "list": [i for i in range(max(1, page - 2), min(page + 2, pagination.num_pages) + 1)],
                "base_url": f"/queue/{selected_line.id}/page/",
            },
            "lines": {
                "list": Lines.all(),
                "current": selected_line,
            },
            "page_title": "Очередь",
            "staff_user": staff_user,
            "errors": errors,
        }
        return render(request, "queue.html", context=context)
