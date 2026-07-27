from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .services import predecir_sensor, predecir_sensores_batch, obtener_sensores_por_distrito, obtener_todos_los_sensores, obtener_evolucion_sensor, obtener_patron_horario_m30, obtener_patron_horario_distrito, obtener_patron_semanal_distrito, obtener_ranking_distritos_historico
import datetime

# PREDICCIONES Y BATCH

class TrafficPredictView(APIView):
    """Endpoint para predecir la ocupación de un sensor individual.    
       Acepta parámetros opcionales por query string: ?fecha=YYYY-MM-DD&hora=0-23
    """
    permission_classes = [AllowAny]

    def get(self, request, id_sensor):
        fecha_str = request.query_params.get("fecha")  # formato esperado: YYYY-MM-DD
        hora_str = request.query_params.get("hora")     # formato esperado: 0-23

        fecha_hora = None
        # Validamos que vengan fecha y hora juntas antes de combinarlas
        if fecha_str and hora_str is not None:
            try:
                fecha = datetime.date.fromisoformat(fecha_str)
                fecha_hora = datetime.datetime.combine(fecha, datetime.time(hour=int(hora_str)))
            except (ValueError, TypeError):
                return Response({"error": "Formato de fecha/hora inválido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultado = predecir_sensor(int(id_sensor), fecha_hora=fecha_hora)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(resultado, status=status.HTTP_200_OK)


class TrafficPredictBatchView(APIView):
    """Predicción para varios sensores en una sola petición POST.
       Espera un body JSON: {"sensores": [1, 2, 3], "fecha": "YYYY-MM-DD", "hora": 0-23}
       ("fecha"/"hora" son opcionales, igual que en TrafficPredictView).
       Devuelve una lista de resultados (uno por sensor con predicción
       disponible), en el mismo formato que TrafficPredictView.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ids_sensores = request.data.get("sensores", [])
        fecha_str = request.data.get("fecha")
        hora_str = request.data.get("hora")

        fecha_hora = None
        if fecha_str and hora_str is not None:
            try:
                fecha = datetime.date.fromisoformat(fecha_str)
                fecha_hora = datetime.datetime.combine(fecha, datetime.time(hour=int(hora_str)))
            except (ValueError, TypeError):
                return Response({"error": "Formato de fecha/hora inválido."}, status=status.HTTP_400_BAD_REQUEST)

        resultados = predecir_sensores_batch(
            [int(s) for s in ids_sensores],
            fecha_hora=fecha_hora,
        )
        return Response(resultados, status=status.HTTP_200_OK)


# CONSULTA DE SENSORES Y DISTRITOS

class TrafficSensoresPorDistritoView(APIView):
    """Retorna la lista de sensores filtrados por un distrito concreto."""
    permission_classes = [AllowAny]

    def get(self, request, id_distrito):
        sensores = obtener_sensores_por_distrito(int(id_distrito))
        if not sensores:
            return Response(
                {"error": f"No hay sensores para el distrito {id_distrito}"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({"id_distrito": id_distrito, "sensores": sensores}, status=status.HTTP_200_OK)


class TrafficTodosSensoresView(APIView):
    """Todos los sensores de Madrid en una sola respuesta.
       Sustituye a hacer 21 llamadas (una por distrito) desde el frontend.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        sensores = obtener_todos_los_sensores()
        return Response({"sensores": sensores}, status=status.HTTP_200_OK)
    

# ENDPOINTS DE ANALÍTICA E HISTÓRICOS

class EvolucionSensorView(APIView):
    """Devuelve la serie temporal histórica de un sensor específico con rango de fechas por defecto."""
    permission_classes = [AllowAny]

    def get(self, request, id_sensor):
        fecha_inicio = request.query_params.get("desde", "2025-07-01")
        fecha_fin = request.query_params.get("hasta", "2026-06-30")
        return Response(
            obtener_evolucion_sensor(int(id_sensor), fecha_inicio, fecha_fin),
            status=status.HTTP_200_OK,
        )


class PatronHorarioDistritoView(APIView):
    """Devuelve el patrón promedio de tráfico hora a hora para un distrito."""
    permission_classes = [AllowAny]

    def get(self, request, id_distrito):
        fecha_inicio = request.query_params.get("desde", "2025-07-01")
        fecha_fin = request.query_params.get("hasta", "2026-06-30")
        return Response(
            obtener_patron_horario_distrito(int(id_distrito), fecha_inicio, fecha_fin),
            status=status.HTTP_200_OK,
        )


class PatronSemanalDistritoView(APIView):
    """Devuelve la distribución de tráfico por día de la semana para un distrito."""
    permission_classes = [AllowAny]

    def get(self, request, id_distrito):
        fecha_inicio = request.query_params.get("desde", "2025-07-01")
        fecha_fin = request.query_params.get("hasta", "2026-06-30")
        return Response(
            obtener_patron_semanal_distrito(int(id_distrito), fecha_inicio, fecha_fin),
            status=status.HTTP_200_OK,
        )


class RankingDistritosView(APIView):
    """Devuelve la lista ordenada de distritos según su nivel de congestión promedio."""
    permission_classes = [AllowAny]

    def get(self, request):
        fecha_inicio = request.query_params.get("desde", "2025-07-01")
        fecha_fin = request.query_params.get("hasta", "2026-06-30")
        return Response(obtener_ranking_distritos_historico(fecha_inicio, fecha_fin), status=status.HTTP_200_OK)


class PatronHorarioM30View(APIView):
    """Devuelve las métricas agregadas específicas para la vía de circunvalación M-30."""
    permission_classes = [AllowAny]

    def get(self, request):
        fecha_inicio = request.query_params.get("desde", "2025-07-01")
        fecha_fin = request.query_params.get("hasta", "2026-06-30")
        return Response(
            obtener_patron_horario_m30(fecha_inicio, fecha_fin), 
            status=status.HTTP_200_OK
        )