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

class HardwareType(models.Model):
    #Human readable name
    name = models.CharField(max_length=50)
    #Image of the hardware
    image = models.ImageField(upload_to='hw_images/')
    #Description of this hardware 
    #what is it used for? which items are contained in the package?
    description = models.TextField()

    def get_available_count(self):
        return HardwareItem.objects.filter(status=HW_AVAILABLE).count()

    def get_requested_count(self):
        return HardwareItem.objects.filter(status=HW_REQUESTED).count()

    def get_lent_count(self):
        return HardwareItem.objects.filter(status=HW_LENT).count()

    def get_unavailable_count(self):
        return HardwareItem.objects.filter(status=HW_UNAVAILABLE).count()

    def __str__(self):
        return self.name

class HardwareItem(models.Model):
    #Hardware model/type
    hardware_type = models.ForeignKey(HardwareType)
    #Identifies a real world object
    label = models.CharField(max_length=20)
    #Status of this item
    status = models.CharField(choices=STATUS, default=HW_AVAILABLE,
                              max_length=1)
    #Any other relevant information about this item
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.label, self.hardware_type.name)

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