from django.shortcuts import render
from django.db.models import *
from django.db import transaction
from control_escolar_desit_api.serializers import MateriaSerializer
from control_escolar_desit_api.models import Materias, Maestros
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
import json
from django.shortcuts import get_object_or_404

class MateriasAll(generics.CreateAPIView):
    #Esta función es esencial para todo donde se requiera autorización de inicio de sesión (token)
    permission_classes = (permissions.IsAuthenticated,)
    # Invocamos la petición GET para obtener todas las materias
    def get(self, request, *args, **kwargs):
        # Obtenemos todas las materias
        materias = Materias.objects.all().order_by("id")
        lista = MateriaSerializer(materias, many=True).data
        for materia in lista:
            if isinstance(materia, dict) and "dias" in materia:
                try:
                    materia["dias"] = json.loads(materia["dias"])
                except Exception:
                    materia["dias"] = []
        return Response(lista, 200)

class MateriasView(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    # Permisos por método (sobrescribe el comportamiento default)
    # Verifica que el usuario esté autenticado para las peticiones GET, PUT y DELETE
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE','PUT']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
    
    #Obtener materia por ID
    def get(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.GET.get("id"))
        data = MateriaSerializer(materia).data
        try:
            data["dias"] = json.loads(data["dias"])
        except Exception:
            data["dias"] = []
        return Response(data, 200)
    
    # Registrar nueva materia
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Extraemos los datos del request
        nrc = request.data["nrc"]
        id_profesor = request.data["profesor"]
        existing_materia=Materias.objects.filter(nrc=nrc).exists()

        # Validación básica
        if existing_materia:
            return Response({"message": "Ya existe una materia con ese NRC"}, 400)

        try:     
            profesor_obj = None
            if id_profesor:
                profesor_obj = Maestros.objects.filter(id=id_profesor).first()
            materia = Materias.objects.create(
                nrc=nrc,
                nombre = request.data["nombre"],
                seccion = request.data["seccion"],
                dias = json.dumps(request.data["dias"]),
                hora_inicio = request.data["hora_inicio"],
                hora_fin = request.data["hora_fin"],
                salon = request.data["salon"],
                programa = request.data["programa"],
                creditos = request.data["creditos"],
                profesor=profesor_obj
            )
            materia.save()
            
            return Response({"message": "Materia registrada correctamente"}, 201)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # Actualizar materia
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        id_materia = request.data.get("id")

        materia = get_object_or_404(Materias, id=id_materia)

        try:
            permission_classes = (permissions.IsAuthenticated,)
            materia.nrc = request.data["nrc"]
            materia.nombre = request.data["nombre"]
            materia.seccion = request.data["seccion"]
            materia.hora_inicio = request.data["hora_inicio"]
            materia.hora_fin = request.data.get["hora_fin"]
            materia.salon = request.data["salon"]
            materia.programa = request.data["programa"]
            materia.creditos = request.data["creditos"]
            materia.dias = json.dumps(request.data["dias"])

            # Actualizar profesor si viene
            id_profesor = request.data["profesor"]
            if id_profesor:
                materia.profesor = Maestros.objects.filter(id=id_profesor).first()
            materia.save()
            return Response({"message": "Materia actualizada correctamente"}, 200)
        except Exception as e:
            return Response({"message": str(e)}, 500)

    # Eliminar materia
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        id_materia = request.GET.get("id")
        materia = get_object_or_404(Materias, id=id_materia)
        try:
            materia.delete()
            return Response({"message": "Materia eliminada"}, 200)
        except Exception as e:
            return Response({"message": "Algo pasó al eliminar"}, 500)