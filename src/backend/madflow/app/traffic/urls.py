from django.urls import path

from .views import (
    EvolucionSensorView,
    PatronHorarioDistritoView,
    PatronHorarioM30View,
    PatronSemanalDistritoView,
    RankingDistritosView,
    TrafficPredictBatchView,
    TrafficPredictView,
    TrafficSensoresPorDistritoView,
    TrafficTodosSensoresView,
)

app_name = 'traffic'

urlpatterns = [
    # Predicciones
    path('traffic/predict/batch/', TrafficPredictBatchView.as_view(), name='traffic-predict-batch'),
    path('traffic/predict/<int:id_sensor>/', TrafficPredictView.as_view(), name='traffic-predict'),
    
    # Sensores y Distritos
    path('traffic/sensores/', TrafficTodosSensoresView.as_view(), name='traffic-todos-sensores'),
    path('traffic/distrito/<int:id_distrito>/sensores/', TrafficSensoresPorDistritoView.as_view(), name='traffic-distrito-sensores'),
    
    # Históricos y Patrones
    path('traffic/historico/ranking-distritos/', RankingDistritosView.as_view(), name='ranking-distritos'),
    path('traffic/historico/patron-horario-m30/', PatronHorarioM30View.as_view(), name='patron-horario-m30'),
    path('traffic/historico/evolucion/<int:id_sensor>/', EvolucionSensorView.as_view(), name='evolucion-sensor'),
    path('traffic/historico/patron-horario-distrito/<int:id_distrito>/', PatronHorarioDistritoView.as_view(), name='patron-horario-distrito'),
    path('traffic/historico/patron-semanal-distrito/<int:id_distrito>/', PatronSemanalDistritoView.as_view(), name='patron-semanal-distrito'),
]