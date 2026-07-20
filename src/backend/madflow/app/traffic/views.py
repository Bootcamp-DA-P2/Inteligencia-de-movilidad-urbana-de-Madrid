from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .services import predecir_sensor, obtener_sensores_por_distrito
import datetime

class TrafficPredictView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id_sensor):
        fecha_str = request.query_params.get("fecha")  # formato esperado: YYYY-MM-DD
        hora_str = request.query_params.get("hora")     # formato esperado: 0-23

        fecha_hora = None
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

# Distrito
class TrafficSensoresPorDistritoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id_distrito):
        sensores = obtener_sensores_por_distrito(int(id_distrito))
        if not sensores:
            return Response(
                {"error": f"No hay sensores para el distrito {id_distrito}"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({"id_distrito": id_distrito, "sensores": sensores}, status=status.HTTP_200_OK)