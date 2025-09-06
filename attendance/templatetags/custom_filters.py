from django import template

register = template.Library()

@register.filter
def get_exam(grades, exam_type):
    """
    Safely get grade for a specific exam_type.
    grades: dictionary or JSON string
    exam_type: string, e.g., 'mid1'
    """
    import json

    # If grades is a string, try to load it as JSON
    if isinstance(grades, str):
        try:
            grades = json.loads(grades)
        except:
            return None

    # Check if grades is a dict
    if isinstance(grades, dict):
        return grades.get(exam_type, None)

    return None
