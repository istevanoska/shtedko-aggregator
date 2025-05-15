"""
URL configuration for DjangoProject3 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    #path('admin/', admin.site.urls),
    path('', include('main.urls')),
]
#koga nema vrednost vo '' znaci deka pristapuvame na pocetnata strana i ne nosi kon main.urls dokumentot kade
#istotaka nemame vrednost na eden path '' i toj ne nosi na view.index funkcijata vo views.py dokumentot
#dokolku sakame da ima drugi strani /mesarnica
#tuka definirame path('', include('main.urls'), dodeka vo main.urls dokumentot
#definirame path path("mesarnica/",views.index,name="index"), potoa vo views.py treba da imame funkcija za mesarnicata sto e html codot