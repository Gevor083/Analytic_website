def theme_processor(request):
    return {
        'theme': request.session.get('theme', 'light')
    }
