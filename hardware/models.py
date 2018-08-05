from django.db import models
from user.models import User
from hardware import settings
from django.utils import timezone
from datetime import timedelta


class ItemType(models.Model):
    """Represents a kind of hardware"""

    #Human readable name
    name = models.CharField(max_length=50, unique=True)
    #Image of the hardware
    image = models.ImageField(upload_to='hw_images/')
    #Description of this hardware 
    #what is it used for? which items are contained in the package?
    description = models.TextField()

    def get_lendable_items(self):
        """ Get items not lent already """
        availables =  Item.objects.filter(item_type=self, available=True)
        lendings = Lending.objects.filter(item__item_type=self, return_time__isnull=True)
        return availables.exclude(id__in=[x.item.id for x in lendings])

    def get_available_count(self):
        ava_count =  Item.objects.filter(item_type=self, available=True).count()
        req_count = self.get_requested_count()
        lent_count = self.get_lent_count()
        return ava_count - req_count - lent_count

    def get_requested_count(self):
        return len(Request.objects.get_active_by_item_type(self))

    def get_lent_count(self):
        return Lending.objects.get_active_by_item_type(self).count()

    def get_unavailable_count(self):
        return Item.objects.filter(item_type=self, available=False).count()

    def make_request(self, user):
        req = Request(item_type=self, user=user)
        req.save()

    def __str__(self):
        return self.name

class Item(models.Model):
    """Represents a real world object identified by label"""

    #Hardware model/type
    item_type = models.ForeignKey(ItemType)
    #Identifies a real world object
    label = models.CharField(max_length=20, unique=True)
    #Is the item available?
    available = models.BooleanField(default=True)
    #Any other relevant information about this item
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.label, self.item_type.name)

class LendingManager(models.Manager):
    def get_active(self):
        return self.get_queryset().filter(return_time__isnull=True)

    def get_active_by_item_type(self, item_type):
        return self.get_queryset().filter(return_time__isnull=True, item__item_type=item_type)

    def get_active_by_user(self, user):
        return self.get_queryset().filter(return_time__isnull=True, user=user)



class Lending(models.Model):
    """ 
    The 'item' has been lent to the 'user' 
    """
    objects = LendingManager()

    user = models.ForeignKey(User)
    #An item can't be lent twice at the same time
    item = models.ForeignKey(Item)
    #Instant of creation
    picked_up_time  = models.DateTimeField(auto_now_add=True)
    #If null: item has not been returned yet
    return_time  = models.DateTimeField(null=True, blank=True)

    def get_picked_up_time_ago(self):
        return str(timezone.now()-self.picked_up_time)
    
    def get_return_time_ago(self):
        return str(timezone.now()-self.return_time)

    def is_active(self):
        return self.return_time is None

    def __str__(self):
        return '{} ({})'.format(self.item.item_type.name, self.user)


class RequestManager(models.Manager):
    def get_active(self):
        return [x for x in self.get_queryset() if x.is_active()]

    def get_active_by_user(self, user):
        qs = self.get_queryset().filter(user=user)
        return [x for x in qs if x.is_active()]

    def get_active_by_item_type(self, item_type):
        qs = self.get_queryset().filter(item_type=item_type)
        return [x for x in qs if x.is_active()]

class Request(models.Model):
    """
    Represents reservation of an item 
    of type 'item_type' done by 'user'
    """

    objects=RequestManager()

    #Requested item type
    item_type = models.ForeignKey(ItemType)
    #Hacker that made the request
    user = models.ForeignKey(User)
    #Lending derived from this request
    lending = models.ForeignKey(Lending, null=True, blank=True)
    #Instant of creation
    request_time = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        delta = timedelta(minutes=settings.REQUEST_TIME) 
        remaining = delta - (timezone.now()-self.request_time)
        return not self.lending and remaining.total_seconds()>0

    def get_remaining_time(self):
        delta = timedelta(minutes=settings.REQUEST_TIME) 
        remaining = delta - (timezone.now()-self.request_time)
        if self.lending:
            return "Lent"
        elif remaining.total_seconds() < 0:
            return "Expired"
        else:
            return str(remaining)

    def __str__(self):
        return '{} ({})'.format(self.item_type, self.user)
