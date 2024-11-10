from django.urls import path
from csvAnalysis import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('',views.home,name="index"),   
]
