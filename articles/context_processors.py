from articles.models import Category


def global_categories(request):
    try:
        categories = Category.objects.filter(is_active=True).order_by('order', 'name')
    except Exception:
        categories = []
    return {'global_categories': categories}
