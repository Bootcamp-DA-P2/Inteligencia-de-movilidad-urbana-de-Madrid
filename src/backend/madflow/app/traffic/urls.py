from django.urls import path
from .views import TrafficPredictView

urlpatterns = [
    path('traffic/predict/<int:id_sensor>/', TrafficPredictView.as_view(), name='traffic-predict'),
]