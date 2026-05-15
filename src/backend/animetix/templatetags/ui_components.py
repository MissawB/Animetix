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
