from django.shortcuts import render

def analytics_dashboard(request):
    return render(request, 'analytics/dashboard.html')

