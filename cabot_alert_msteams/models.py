import logging
from os import environ as env

import requests
from cabot.cabotapp.alert import AlertPlugin
from django.conf import settings
from django.template import Context, Template

logger = logging.getLogger(__name__)

msteams_template = "Service {{ service.name }} {% if service.overall_status == service.PASSING_STATUS %}is back to normal{% else %}reporting {{ service.overall_status }} status{% endif %}: {{ scheme }}://{{ host }}{% url 'service' pk=service.id %}. {% if service.overall_status != service.PASSING_STATUS %}Checks failing: {% for check in service.all_failing_checks %}{% if check.check_category == 'Jenkins check' %}{% if check.last_result.error %} {{ check.name }} ({{ check.last_result.error|safe }}) {{jenkins_api}}job/{{ check.name }}/{{ check.last_result.job_number }}/console{% else %} {{ check.name }} {{jenkins_api}}/job/{{ check.name }}/{{check.last_result.job_number}}/console {% endif %}{% else %} {{ check.name }} {% if check.last_result.error %} ({{ check.last_result.error|safe }}){% endif %}{% endif %}{% endfor %}{% endif %}{% if alert %}{% for alias in users %} @{{ alias }}{% endfor %}{% endif %}"


# This provides the hipchat alias for each user. Each object corresponds to a User
class MSTeamsAlert(AlertPlugin):
    name = "MSTeams"
    author = "Ioannis Mavroukakis"

    def send_alert(self, service, users, duty_officers):
        alert = True
        users = list(users) + list(duty_officers)
        color = 'green'

        if service.overall_status == service.WARNING_STATUS:
            color = 'orange'

        if service.overall_status == service.ERROR_STATUS:
            if service.old_overall_status in (service.ERROR_STATUS, service.ERROR_STATUS):
                alert = False  # Don't alert repeatedly for ERROR

        if service.overall_status == service.PASSING_STATUS:
            color = 'green'
            if service.old_overall_status == service.WARNING_STATUS:
                alert = False  # Don't alert for recovery from WARNING status
        else:
            color = 'red'

        c = Context({
            'service': service,
            'users': users,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME,
            'alert': alert,
            'jenkins_api': settings.JENKINS_API,
        })
        message = Template(msteams_template).render(c)
        self._send_msteams_alert(message, service.name, color=color, sender='Cabot/%s' % service.name)

    def _send_msteams_alert(self, message, service, color='green', sender='Cabot'):

        if not env.get('MSTEAMS_ALERT_URL'):
            logger.warn("MSTEAMS_ALERT_URL webhook url is not defined")
            raise Exception("MSTEAMS_ALERT_URL webhook url is not defined")

        url = env.get('MSTEAMS_ALERT_URL')

        logger.warn('Sending to MSTeams ' + url)
        
        data = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000",
            "summary": "Status"
        }
        
        logger.debug(data)

        resp = requests.post(url, data)
        logger.warn('MSTeams response ' + resp.text)
