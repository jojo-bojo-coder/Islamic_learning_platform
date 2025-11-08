from .models import DirectorAlert
def director_context(request):
    context = {}
    if request.user.is_authenticated and request.user.role == 'director':
        unread_alerts_count = DirectorAlert.objects.filter(is_read=False).count()
        context['unread_alerts_count'] = unread_alerts_count
    return context