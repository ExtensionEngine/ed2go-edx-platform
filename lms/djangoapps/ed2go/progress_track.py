from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator

from .models import CompletionProfile
from .utils import extract_course_id_from_url, extract_problem_id

EVENT_BLOCK_MAP = {
    'stop_video': 'video',
    'problem_check': 'problem',
}


def track_user_event(user, event_name, data, page):
    """
    Marks a user's progress in the user's CompletionProfile whenever an
    appropriate event is logged, and sends the report to the third-party API.

    Args:
        user (User): the user object.
        event_name (str): the name of the logged event. Event names are specific to
            edX events and are mapped to the events tracked for the completion report.
        data (str or dict): in the event of a watched video, edX logs data in a dict
            where the `id` key contains the video block ID. For problems edX concatinates
            the problem block ID with additional data and the ID is extracted with
            `extract_problem_id()`
        page (str): URL where the event was triggered. Used to extract the course ID.
    """
    if event_name in EVENT_BLOCK_MAP:
        block_type = EVENT_BLOCK_MAP[event_name]
        course_id = extract_course_id_from_url(page)
        course_key = CourseKey.from_string(course_id)
        if block_type == 'problem':
            data_id = extract_problem_id(data)
        elif block_type == 'video':
            data_id = data['id']
        else:
            raise Exception('Block type %s not supported.' % block_type)
        usage_key = BlockUsageLocator(course_key, block_type, data_id)

        completion_info, _ = CompletionProfile.objects.get(user=user, course_key=course_key)
        completion_info.mark_progress(block_type, str(usage_key))
        completion_info.send_report()
