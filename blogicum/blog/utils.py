from django.core.paginator import Paginator


def paginate(request, queryset, items=10):
    paginator = Paginator(queryset, items)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
