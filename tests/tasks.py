from sprinklers.base import SprinklerBase, ShardedSprinkler, registry, SubtaskValidationException
from tests.models import DummyModel
from celery import task
from traceback import format_exc


@task
def run_sample_sprinkler(**kwargs):
    SampleSprinkler(**kwargs).start()

@task
def run_sharded_sprinkler(**kwargs):
    ShardedSampleSprinkler(**kwargs).start()

class SampleSprinkler(SprinklerBase):

    def get_queryset(self):
        """
        This IF normally wouldn't be necessary because you either would or wouldn't be passing kwargs
        into the sprinkler. But I have tests that sometimes do and sometimes don't use kwargs, hence the
        check.
        """
        if self.kwargs.get('name', None):
            return DummyModel.objects.filter(name=self.kwargs['name']).all()
        if self.kwargs.get('values', None):
            return DummyModel.objects.all().values('id')
        return DummyModel.objects.all()

    def subtask(self, obj):
        if self.kwargs.get('raise_error') and obj.name == 'fail':
            raise AttributeError("Oh noes!")
        obj.name = "Sprinkled!"
        obj.save()
        if self.kwargs.get('special_return'):
            return True

    def validate(self, obj):
        if self.kwargs.get('fail'):
            raise SubtaskValidationException

    def on_validation_exception(self, obj, e):
        return "v_fail"

    def finished(self, results):
        # Persist results to an external source (the database) so I can unit test this.
        # Note that it writes the entire result obj as the name
        if self.kwargs.get('persist_results'):
            DummyModel(name="%s" % results).save()

    def on_error(self, obj, e):
        print("Here's the error: " + format_exc())
        return False

registry.register(SampleSprinkler)

class ShardedSampleSprinkler(ShardedSprinkler):
    shard_size = 2

    def get_queryset(self):
        if self.kwargs.get('name', None):
            return DummyModel.objects.filter(name=self.kwargs['name'])

        return DummyModel.objects.all()

    def subtask(self, obj):
        if self.kwargs.get('raise_error') and obj.name == 'fail':
            raise AttributeError("Oh noes!")

        obj.name = "Sharded!"
        obj.save()

        if self.kwargs.get('special_return'):
            return True

    def validate(self, obj):
        if self.kwargs.get('fail'):
            raise SubtaskValidationException

    def on_validation_exception(self, obj, e):
        return "v_fail"

    def finished(self, results):
        # Persist results to an external source (the database) so I can unit test this.
        # Note that it writes the entire result obj as the name

        if self.kwargs.get('persist_results'):
            DummyModel(name="%s" % results).save()

    def on_error(self, obj, e):
        print("Here's the error: " + format_exc())
        return False

registry.register(ShardedSampleSprinkler)
