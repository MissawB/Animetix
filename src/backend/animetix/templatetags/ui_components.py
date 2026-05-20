from django import template
from django.urls import reverse

register = template.Library()

@register.inclusion_tag('animetix/partials/search_bar.html')
def search_bar(action_url_name, placeholder, media_type=None, input_id='guess-input'):
    """
    Renders a server-side autocomplete search bar.
    
    Args:
        action_url_name: The name of the URL to POST the guess to.
        placeholder: Placeholder text for the input.
        media_type: Optional filter for the autocomplete API.
        input_id: HTML ID for the input element.
    """
    return {
        'action_url': reverse(action_url_name),
        'placeholder': placeholder,
        'media_type': media_type or '',
        'input_id': input_id
    }

@register.inclusion_tag('animetix/partials/character_card.html')
def character_card(mode_data, index=0):
    """
    Renders a character-styled card for game modes.
    """
    return {'mode': mode_data, 'index': index}

@register.inclusion_tag('animetix/partials/user_profile_card.html', takes_context=True)
def user_profile_card(context):
    """
    Renders the user profile card with level and XP progress.
    """
    return {'request': context.get('request')}

@register.inclusion_tag('animetix/partials/achievement_toast.html')
def achievement_toast(achievement):
    """
    Renders a single achievement toast.
    """
    return {'ach': achievement}
