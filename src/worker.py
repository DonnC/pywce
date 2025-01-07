from src.models import WorkerJob


class Worker:
    """
        main engine worker class

        handles processing a single webhook request, process template
        and send request back to WhatsApp
    """

    def __init__(self, job: WorkerJob):
        self.job = job
        self.work()

    def work(self):
        # worker work entry processor
        # TODO: handle all processes here
        pass
