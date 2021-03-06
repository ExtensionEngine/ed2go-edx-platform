from dateutil import parser

from django.contrib.auth.models import User
from student.models import UserProfile

from ed2go import constants as c
from ed2go.models import CompletionProfile


def update_registration(registration_data):
    """
    Update the user information:
        * name
        * country
        * year_of_birth
        * ReturnURL
        * StudentKey

    Update the reference ID in the Completion Profile.

    Args:
        registration_data (dict): The registration data from ed2go.

    Returns:
        The completion profile.
    """
    student_data = registration_data[c.REG_STUDENT]
    user = User.objects.get(email=student_data[c.REG_EMAIL])

    user.first_name = student_data[c.REG_FIRST_NAME]
    user.last_name = student_data[c.REG_LAST_NAME]

    profile = UserProfile.objects.get(user=user)
    profile.name = student_data[c.REG_FIRST_NAME] + ' ' + student_data[c.REG_LAST_NAME]
    profile.country = student_data[c.REG_COUNTRY]
    if student_data[c.REG_BIRTHDATE]:
        profile.year_of_birth = parser.parse(student_data[c.REG_BIRTHDATE]).year
    else:
        profile.year_of_birth = None

    meta = profile.get_meta() if profile.meta else {}
    meta['ReturnURL'] = registration_data[c.REG_RETURN_URL]
    meta['StudentKey'] = registration_data[c.REG_STUDENT][c.REG_STUDENT_KEY]
    profile.set_meta(meta)
    profile.save()

    registration_key = registration_data[c.REG_REGISTRATION_KEY]
    completion_profile = CompletionProfile.objects.get(registration_key=registration_key)
    completion_profile.reference_id = registration_data[c.REG_REFERENCE_ID]
    completion_profile.save()

    return completion_profile
