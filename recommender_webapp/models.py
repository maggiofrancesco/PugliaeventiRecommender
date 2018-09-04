from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from recommender_webapp.common import constant
from recommender_webapp.common.utils import ChoiceEnum
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import User, AbstractUser


DEFAULT_RATING = 3


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model."""

    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()


class Profile(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL)
    location = models.CharField(max_length=40, blank=False)
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profession = models.CharField(max_length=40, blank=True)
    empathy = models.FloatField(null=True, blank=True)
    first_configuration = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user.email) + '|' + self.location + '|' + self.birth_date.strftime('%d/%m/%Y')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Place(models.Model):
    placeId = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, blank=False)
    location = models.CharField(max_length=40, blank=False)
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

    def labels(self):
        labels = ""
        if self.freeEntry:
            labels += constant.FREE_ENTRY + ', '
        if self.bere:
            labels += constant.BERE + ', '
        if self.mangiare:
            labels += constant.MANGIARE + ', '
        if self.benessere:
            labels += constant.BENESSERE + ', '
        if self.dormire:
            labels += constant.DORMIRE + ', '
        if self.goloso:
            labels += constant.GOLOSO + ', '
        if self.libri:
            labels += constant.LIBRI + ', '
        if self.romantico:
            labels += constant.ROMANTICO + ', '
        if self.museo:
            labels += constant.MUSEO + ', '
        if self.spiaggia:
            labels += constant.SPIAGGIA + ', '
        if self.teatro:
            labels += constant.TEATRO + ', '
        return labels

    def __str__(self):
        return str(self.placeId) + '|' + self.name + '|' + self.location


class Mood(ChoiceEnum):
    __order__ = 'angry joyful sad'
    angry = 1
    joyful = 2
    sad = 3


class Companionship(ChoiceEnum):
    __order__ = 'withFriends alone'
    withFriends = 1
    alone = 2


class Rating(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Profile, on_delete=models.PROTECT, blank=False)
    mood = models.CharField(max_length=20, choices=Mood.choices(), blank=False)
    companionship = models.CharField(max_length=20, choices=Companionship.choices(), blank=False)
    companionship = models.CharField(max_length=20, choices=Companionship.choices(), blank=False)
    place = models.ForeignKey(Place, on_delete=models.PROTECT, blank=False)
    rating = models.IntegerField(blank=False, default=DEFAULT_RATING)

    # class Meta:
    #    unique_together = ('user', 'mood', 'companionship', 'place')

    def __str__(self):
        return str(self.user.email) + '|' + str(self.mood) + '|' + str(self.companionship) \
               + '|' + str(self.place.placeId) + '|' + str(self.rating)


class SampleRating(models.Model):
    id = models.AutoField(primary_key=True)
    userId = models.IntegerField(blank=False)
    placeId = models.ForeignKey(Place, on_delete=models.PROTECT, blank=False)
    rating = models.IntegerField(blank=False)

    class Meta:
        unique_together = ('userId', 'placeId')


class Comune(models.Model):
    istat = models.CharField(max_length=7, primary_key=True)
    nome = models.CharField(max_length=100, blank=False)
    provincia = models.CharField(max_length=3, blank=False)
    regione = models.CharField(max_length=4, blank=False)
    prefisso = models.CharField(max_length=6)
    cap = models.CharField(max_length=6)
    cod_fis = models.CharField(max_length=6)
    abitanti = models.IntegerField()


class Distanza(models.Model):
    cittaA = models.CharField(max_length=100, blank=False)
    cittaB = models.CharField(max_length=100, blank=False)
    distanza = models.FloatField()
