# home/middleware.py
class NotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(request, 'user') and request.user.is_authenticated:
            response.context_data['has_unread_notifications'] = \
                request.user.notifications.filter(statut='NON_LU').exists()
        return response
    