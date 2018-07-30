from django.db import models
from user.models import User

#A hacker can request this hardware
HW_AVAILABLE = 'A'
#A hacker requested this hardware and it's reserved for a time
HW_REQUESTED = 'R'
#A hacker has this hardware
HW_LENT = 'L'
#This hardware is unavailable for any other reasons
HW_UNAVAILABLE = 'U'

STATUS = [
    (HW_AVAILABLE, 'Available'),
    (HW_REQUESTED, 'Requested'),
    (HW_LENT, 'Lent'),
    (HW_UNAVAILABLE, 'Unavailable'),
]

class HardwareItem(models.Model):
    #Identifies a real world object
    label = models.CharField(max_length=20)
    #Human readable name
    label = models.CharField(max_length=40)
    #Status of this item
    status = models.CharField(choices=STATUS, default=HW_AVAILABLE,
                              max_length=1)
    #Any other relevant information about this item
    comments = models.TextField(blank=True, null=True)

class LogMessage(models.Model):
    user = models.ForeignKey(User)
    item = models.ForeignKey(HardwareItem)
    #Status previous to this event
    old_status = models.CharField(choices=STATUS, default=HW_AVAILABLE,
                              max_length=1)
    #New status
    new_status = models.CharField(choices=STATUS, default=HW_AVAILABLE,
                              max_length=1)

    instant = models.DateField(auto_now_add=True)