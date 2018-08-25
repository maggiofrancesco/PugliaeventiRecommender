from django.db import models
from django.contrib.auth.models import User

from recommender.common.utils import ChoiceEnum


class Profile(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    userId = models.AutoField(primary_key=True)
    location = models.CharField(max_length=30, blank=False)
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profession = models.CharField(max_length=40, blank=True)
    empathy = models.FloatField()

    def __str__(self):
        return str(self.userId) + '|' + self.location + '|' + self.birth_date.strftime('%d/%m/%Y')


class Place(models.Model):
    placeId = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, blank=False)
    location = models.CharField(max_length=30, blank=False)
    freeEntry = models.BooleanField()
    bere = models.BooleanField()
    mangiare = models.BooleanField()
    benessere = models.BooleanField()
    dormire = models.BooleanField()
    goloso = models.BooleanField()
    libri = models.BooleanField()
    romantico = models.BooleanField()
    museo = models.BooleanField()
    spiaggia = models.BooleanField()
    teatro = models.BooleanField()

    def __str__(self):
        return str(self.placeId) + '|' + self.name + '|' + self.location


class Mood(ChoiceEnum):
    angry = 1
    joyful = 2
    sad = 3


class Companionship(ChoiceEnum):
    withFriends = 1
    alone = 2


class Rating(models.Model):
    id = models.AutoField(primary_key=True)
    userId = models.ForeignKey(Profile, on_delete=models.PROTECT, blank=False)
    mood = models.CharField(max_length=1, choices=Mood.choices(), blank=False)
    companionship = models.CharField(max_length=1, choices=Companionship.choices(), blank=False)
    placeId = models.ForeignKey(Place, on_delete=models.PROTECT, blank=False)
    rating = models.IntegerField(blank=False)

    class Meta:
        unique_together = ('userId', 'mood', 'companionship', 'placeId')

    def __str__(self):
        return str(self.userId) + '|' + str(self.mood) + '|' + str(self.companionship) \
               + '|' + str(self.placeId) + '|' + str(self.rating)
