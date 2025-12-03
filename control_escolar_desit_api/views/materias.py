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
            if "dias" in materia and materia["dias"]:
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
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  # POST no requiere autenticación
    
    #Obtener materia por ID
    def get(self, request, *args, **kwargs):
        id_materia = request.GET.get("id")
        if not id_materia:
            return Response({"message": "ID no proporcionado"}, 400)
        
        materia = get_object_or_404(Materias, id=id_materia)
        serializer = MateriaSerializer(materia)
        data = serializer.data
        # Convertir el string JSON de días a una lista real
        if "dias" in data and data["dias"]:
            try:
                data["dias"] = json.loads(data["dias"])
            except Exception:
                data["dias"] = []
                
        return Response(data, 200)
    
    # Registrar nueva materia
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Extraemos los datos del request
        nrc = request.data.get("nrc")
        nombre = request.data.get("nombre")
        seccion = request.data.get("seccion")
        dias_list = request.data.get("dias")
        hora_inicio = request.data.get("hora_inicio")
        hora_fin = request.data.get("hora_fin")
        salon = request.data.get("salon")
        programa = request.data.get("programa")
        creditos = request.data.get("creditos")
        id_profesor = request.data.get("profesor")
        existing_materia=Materias.objects.filter(nrc=nrc).exists()

        # Validación básica
        if existing_materia:
            return Response({"message": "Ya existe una materia con ese NRC"}, 400)

        try:
            # Convertimos la lista de días a JSON String
            dias_json = json.dumps(dias_list) if dias_list else "[]"
            
            profesor_obj = None
            if id_profesor:
                profesor_obj = Maestros.objects.filter(id=id_profesor).first()
            materia = Materias.objects.create(
                nrc=nrc,
                nombre=nombre,
                seccion=seccion,
                dias=dias_json,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                salon=salon,
                programa=programa,
                creditos=creditos,
                profesor=profesor_obj
            )
            materia.save()
            
            return Response({"message": "Materia registrada correctamente"}, 201)
        except Exception as e:
            return Response({"message": str(e)}, 500)

    # Actualizar materia
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        id_materia = request.data.get("id")
        if not id_materia:
             return Response({"message": "ID de materia no proporcionado"}, 400)
        materia = get_object_or_404(Materias, id=id_materia)

        try:
            permission_classes = (permissions.IsAuthenticated,)
            materia.nrc = request.data.get("nrc", materia.nrc)
            materia.nombre = request.data.get("nombre", materia.nombre)
            materia.seccion = request.data.get("seccion", materia.seccion)
            materia.hora_inicio = request.data.get("hora_inicio", materia.hora_inicio)
            materia.hora_fin = request.data.get("hora_fin", materia.hora_fin)
            materia.salon = request.data.get("salon", materia.salon)
            materia.programa = request.data.get("programa", materia.programa)
            materia.creditos = request.data.get("creditos", materia.creditos)
            
            # Si se envían días nuevos, los actualizamos
            dias_list = request.data.get("dias")
            if dias_list is not None:
                materia.dias = json.dumps(dias_list)

            # Actualizar profesor si viene
            id_profesor = request.data.get("profesor")
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
        if not id_materia:
            return Response({"message": "ID no proporcionado"}, 400)
        materia = get_object_or_404(Materias, id=id_materia)
        try:
            materia.delete()
            return Response({"message": "Materia eliminada"}, 200)
        except Exception as e:
            return Response({"message": "Algo pasó al eliminar"}, 500)