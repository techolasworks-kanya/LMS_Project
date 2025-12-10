from django.shortcuts import render
from LMS_app.models import *
from LMS_app.serializers import *
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

# Create your views here.
