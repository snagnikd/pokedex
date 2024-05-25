from django.db import models


class Record(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	id = models.CharField(max_length=5, primary_key=True)
	name = models.CharField(max_length=30)
	experience =  models.CharField(max_length=10, default=0)
	height =  models.CharField(max_length=10)
	image_url = models.CharField(max_length=200)
	description = models.CharField(max_length=400)

	def __str__(self):
		return(f"{self.first_name} {self.last_name}")
