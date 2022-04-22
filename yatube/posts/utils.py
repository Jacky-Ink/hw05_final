from django.core.paginator import Paginator
from yatube.settings import NUMBER_OF_POSTS


def paginator_of_page(request, posts):
    """Модуль отвечающий за разбитие текта на страницы."""
    paginator = Paginator(posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
