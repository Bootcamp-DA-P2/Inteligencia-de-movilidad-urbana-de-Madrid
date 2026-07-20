from django.urls import path
from .views import TrafficPredictView
from .views import TrafficSensoresPorDistritoView

urlpatterns = [
    path('traffic/predict/<int:id_sensor>/', TrafficPredictView.as_view(), name='traffic-predict'),    
    path('traffic/distrito/<int:id_distrito>/sensores/', TrafficSensoresPorDistritoView.as_view(), name='traffic-distrito-sensores'),
]