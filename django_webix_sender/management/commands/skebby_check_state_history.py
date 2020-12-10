# -*- coding: utf-8 -*-

import time

from django.core.management import BaseCommand

from django_webix_sender.send_methods.skebby.tasks import check_state_history


class Command(BaseCommand):
    help = "Check unknown status messages from Skebby history"

    def add_arguments(self, parser):
        parser.add_argument('--all-sender-name', action='store_true')

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write("Check unknown status messages from Skebby history")
        results = check_state_history(same_sender_name=not options['all_sender_name'])
        if 'status' in results:
            self.stdout.write(self.style.WARNING("Error: {}".format(results['status'])))
        if 'remaining' in results:
            self.stdout.write("Remaining: {}".format(results['remaining']))
        self.stdout.write("--- %s seconds ---" % (time.time() - start_time))
