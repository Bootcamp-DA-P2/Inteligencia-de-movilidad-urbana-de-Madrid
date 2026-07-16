from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .services import predecir_sensor

class TrafficPredictView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id_sensor):
        try:
            resultado = predecir_sensor(int(id_sensor))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(resultado, status=status.HTTP_200_OK)