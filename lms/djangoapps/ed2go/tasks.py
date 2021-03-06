from datetime import timedelta

import requests
from celery import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils.timezone import now
from waffle import switch_is_active

from ed2go import constants as c
from ed2go.models import CompletionProfile, CourseSession
from ed2go.xml_handler import XMLHandler

LOG = get_task_logger(__name__)
THRESHOLD = timedelta(seconds=settings.ED2GO_SESSION_INACTIVITY_THRESHOLD)


@task()
def check_course_sessions():
    """
    Periodic task to close any active sessions whose last activity was longer
    than the THRESHOLD.
    """
    qs = CourseSession.objects.filter(active=True)  # pylint: disable=invalid-name
    thresholded_time = now() - THRESHOLD
    for obj in qs:
        if obj.last_activity_at < thresholded_time:
            obj.close(offset_delta=THRESHOLD)


@task()
def send_completion_report():
    """
    Periodic task to send completion reports to ed2go.
    """
    if switch_is_active(c.ENABLED_ED2GO_COMPLETION_REPORTING):
        qs = CompletionProfile.objects.filter(to_report=True)  # pylint: disable=invalid-name
        xmlh = XMLHandler()
        xml_data = []

        for obj in qs:
            report = obj.report
            report[c.REQ_API_KEY] = settings.ED2GO_API_KEY
            xml_data.append(
                xmlh.xml_from_dict({c.REQ_UPDATE_COMPLETION_REPORT: report})
            )

        request_data = xmlh.request_data_from_xml(''.join(xml_data))
        response = requests.post(
            url=settings.ED2GO_REGISTRATION_SERVICE_URL,
            data=request_data,
            headers=xmlh.headers
        )
        if response.status_code == 200:
            response_data = xmlh.get_response_data_from_xml(
                response_name=c.RESP_UPDATE_COMPLETION_REPORT,
                xml=response.content
            )
            if response_data[c.RESP_SUCCESS] == 'true':
                LOG.info('Sent batch completion report update.')
                qs.update(to_report=False)
                return True
        LOG.error('Failed to send batch completion report update.')
        return False
