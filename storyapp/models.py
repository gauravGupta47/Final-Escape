from django.db import models

class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class Theme(TimeStampModel):
    name = models.CharField(max_length=100)
    description = models.TextField(help_text="Used to prompt GPT")

    def __str__(self):
        return self.name


class User(TimeStampModel):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email


class Story(TimeStampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='stories')
    character_name = models.CharField(max_length=100)
    plot_text = models.TextField(help_text="Generated by GPT")
    plot_image_path = models.CharField(max_length=255, null=True, blank=True, help_text="Image generated using SD")
    pdf_path = models.CharField(max_length=255, null=True, blank=True)
    email_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.character_name}'s {self.theme.name} story"


class StoryResponse(TimeStampModel):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='responses')
    user_input = models.TextField()
    ai_response = models.TextField(help_text="Text from GPT")
    user_img_path = models.CharField(max_length=255, null=True, blank=True, help_text="Comic image for user input")
    ai_img_path = models.CharField(max_length=255, null=True, blank=True, help_text="Comic image for AI reply")
    
    def __str__(self):
        return f"Response {self.id} for {self.story}"
