from django.db import models
from user.models import User
from hardware import settings
from django.utils import timezone
from datetime import timedelta

#A hacker can request this hardware
HW_AVAILABLE = 'A'
#A hacker has this hardware
HW_LENT = 'L'
#This hardware is unavailable for any other reasons
HW_UNAVAILABLE = 'U'

STATUS = [
    (HW_AVAILABLE, 'Available'),
    (HW_LENT, 'Lent'),
    (HW_UNAVAILABLE, 'Unavailable'),
]

class ItemType(models.Model):
    """Represents a kind of hardware"""

    #Human readable name
    name = models.CharField(max_length=50, unique=True)
    #Image of the hardware
    image = models.ImageField(upload_to='hw_images/')
    #Description of this hardware 
    #what is it used for? which items are contained in the package?
    description = models.TextField()

    def get_available_count(self):
        available_count = Item.objects.filter(item_type=self, status=HW_AVAILABLE).count()
        requested_count = self.get_requested_count()
        return available_count - requested_count

    def get_requested_count(self):
        time_threshold = timezone.now() - timedelta(minutes=settings.REQUEST_TIME)
        return Request.objects.filter(item_type=self, timestamp__gte=time_threshold).count()

    def get_lent_count(self):
        return Item.objects.filter(item_type=self, status=HW_LENT).count()

    def get_unavailable_count(self):
        return Item.objects.filter(item_type=self, status=HW_UNAVAILABLE).count()

    def __str__(self):
        return self.name

class Item(models.Model):
    """Represents a real world object identified by label"""

    #Hardware model/type
    item_type = models.ForeignKey(ItemType)
    #Identifies a real world object
    label = models.CharField(max_length=20, unique=True)
    #Status of this item
    status = models.CharField(choices=STATUS, default=HW_AVAILABLE,
                              max_length=1)
    #Any other relevant information about this item
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.label, self.item_type.name)

class Request(models.Model):
    """Represents a request (a reservation for a certain amount of time)"""

    #Requested item type
    item_type = models.ForeignKey(ItemType)
    #Hacker that made the request
    user = models.ForeignKey(User)
    #Instant of creation
    timestamp = models.DateTimeField(auto_now_add=True)

    def get_remaining_time(self):
        delta = timedelta(minutes=settings.REQUEST_TIME) 
        remaining = delta - (timezone.now()-self.timestamp)
        if remaining.total_seconds() < 0:
            return "Expired"
        else:
            return str(remaining)

    def __str__(self):
        return '{} ({})'.format(self.item_type, self.user)

class LogMessage(models.Model):
    """Represents a change of status in time"""

    user = models.ForeignKey(User)
    item = models.ForeignKey(Item)
    #Status previous to this event
    old_status = models.CharField(choices=STATUS, default=HW_AVAILABLE,
                              max_length=1)
    #New status
    new_status = models.CharField(choices=STATUS, default=HW_AVAILABLE,
                              max_length=1)

    instant = models.DateField(auto_now_add=True)